"""
Simulation region calling algorithms

algorithms:
    diff_ttest
"""

import sys
import multiprocessing as mp
from itertools import product, islice, repeat

if sys.version_info <= (3, 0):
    from itertools import izip as zip

import numpy as np
from scipy import stats

from helpers import get_logger, grouper

log = get_logger(__name__)

n_cpu = mp.cpu_count()


def _diff_ttest(position, time_series, break_points, direction='+',
                n_before=None, n_after=None, phase=0, diff_length=1):
    """
    perform diff_ttest algorithm on time_series, return (position, pvalue) pair

    :position: spatial position (y, x, z)
    :time_series: (1D numpy array)
    :break_points: (tuple) index number of image when event start and end.
    :direction: ('+'/'-'/'~') '+' for simulation region '-' for suppression region,
        '~' for not consider direction
    :n_before: (int) how many images to consider before the event occur.
    :n_after: (int) how many images to consider in the phase after event occur.
    :phase: (int) phase number.
    :diff_length: (int)
    """
    break_start, break_end = break_points
    if n_before:
        before = time_series[break_start-n_before : break_start]
    else:
        before = time_series[:break_start]
    if n_after:
        after = time_series[break_end+1 : break_end+n_after+1]
    else:
        after = time_series[break_end+1:]
    diff_before = np.diff(before)
    diff_after = np.diff(after)
    T = stats.ttest_ind(diff_after, diff_before)
    if direction == '+':
        pvalue = T[1] if T[0] > 0 else 1
    elif direction == '-':
        pvalue = T[1] if T[0] < 0 else 1
    else:
        pvalue = T[1]
    return position, pvalue


def _ttest(position, time_series, intervals, direction='+'):
    """
    perform ttest algorithm, return (position, pvalue) pair

    :position: spatial position (y, x, z)
    :time_series: (1D numpy array)
    :intervals: (list) a list of intervals. like: [(0, 10), (30, 50), (100, 110)]
    :direction: ('+'/'-'/'~') '+' for simulation region '-' for suppression region,
        '~' for not consider direction
    """
    # create simulation points mask
    mask = np.zeros(shape=time_series.shape)
    for s, e in intervals:
        mask[s:e] = 1
    series_simu = time_series[mask == 1]
    series_background = time_series[mask == 0]
    T = stats.ttest_ind(series_simu, series_background)
    if direction == '+':
        pvalue = T[1] if T[0] > 0 else 1
    elif direction == '-':
        pvalue = T[1] if T[0] < 0 else 1
    else:
        pvalue = T[1]
    return position, pvalue


def algorithm_interface(alg_func, series, processes=1, *args, **kwargs):
    """
    Heleper function provide a middle layer for call algorithm function.

    :alg_func: algotirhm function like `call_simu._diff_ttest`.
    :series: `simucaller.series.Series` object.
    :processes: use how many cpu cores perform algorithm.

    """
    # construct arguments
    nt, ny, nx, nz = series.shape
    points = product(range(ny), range(nx), range(nz))
    size = ny * nx * nz

    # read series
    #
    # IO is soo slow, so read all information at once here...
    arr4d = series.h5dict['arr4d'][...]
    time_series = [arr4d[:, y, x, z]
                   for y, x, z in product(range(ny), range(nx), range(nz))]

    # construct args repeat
    rep_args = [points, time_series] + [repeat(arg, size) for arg in args]
    rep_args = zip(*rep_args)
    rep_kwargs = repeat(kwargs, size)

    # call algorithm
    if processes == 1:
        results = []
        for _args, _kwargs in zip(rep_args, rep_kwargs):
            result = alg_func(*_args, **_kwargs)
            results.append(result)
    else:
        raise NotImplementedError # one cpu core seem enough
        #chunked_args = grouper(args, 10000)

        #def worker(args_chunk):
        #    result = []
        #    for arg in args_chunk:
        #        res = _diff_ttest(*arg)
        #        result.append(res)
        #    return result

        #pool = mp.Pool(processes=processes)
        #log.info("{} processes spawned.".format(processes))

        #results = []
        #def collect_results(res_chunk):
        #    for res in res_chunk:
        #        results.append(res)

        #for args_chunk in chunked_args:
        #    pool.apply_async(worker, args=args_chunk, callback=collect_results)

        #pool.close()
        #pool.join()
        #results.sort(key=lambda t: t[0])

    # sort according to position
    results = [p for pos, p in results]
    assert size == len(results)

    # reshape to 3D
    pvalue_arr3d = np.asarray(results)
    pvalue_arr3d = pvalue_arr3d.reshape((ny, nx, nz))
    return pvalue_arr3d


def diff_ttest(series, direction='+', n_before=None, n_after=None,
               phase=1, diff_length=1):
    """
    'diff_ttest' algorithm interface

    :series: (simucaller.Series object)
    """
    assert hasattr(series, 'break_points'),\
        "Please run series.set_break_point firstly"

    pvalue_arr3d = algorithm_interface(_diff_ttest,
        series, processes=1,
        break_points=series.break_points,
        direction='+', n_before=None, n_after=None, phase=0, diff_length=1)

    return pvalue_arr3d


def ttest(series, direction='+'):
    """
    ttest algorithm interface

    :series: (simucaller.Series object)
    """
    assert hasattr(series, 'simu_intervals'),\
        "Please run series.set_sumu_intervals firstly"

    pvalue_arr3d = algorithm_interface(_ttest,
        series, processes=1,
        intervals=series.simu_intervals, direction='+')

    return pvalue_arr3d
