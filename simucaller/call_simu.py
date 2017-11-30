"""
Simulation region calling algorithms

algorithms:
    diff_ttest
"""

import multiprocessing as mp
from itertools import product, islice

import numpy as np
from scipy import stats

from helpers import get_logger

log = get_logger(__name__)

n_cpu = mp.cpu_count()

def _diff_ttest(time_series, break_point, n_before, n_after, phase=0, diff_length=1):
    """
    perform diff_ttest algorithm on time_series
    :time_series: (1D numpy array)
    :break_point: (int) index number of image when event occur.
    :n_before: (int) how many images to consider before the event occur.
    :n_after: (int) how many images to consider in the phase after event occur.
    :phase: (int) phase number.
    :diff_length: (int)
    """
    before = time_series[:break_point]
    after = time_series[break_point+1:]
    diff_before = before.diff()
    diff_after = after.diff()
    T = stats.ttest_ind(diff_after, diff_before)
    pvalue = T[0]
    return pvalue

def diff_ttest(series, processes=n_cpu):
    """
    :series: (simucaller.Series object)
    :processes: use how many cpu cores
    """
    assert hasattr(series, 'break_point'),\
        "Please run series.set_break_point firstly"
    pool = mp.Pool(processes=processes)
    log.info("{} processes spawned.".format(processes))
    nt, ny, nx, nz = series.shape
    points = product(range(ny), range(nx), range(nz))
    result = []
    while True:
        batch_points = islice(points, processes * 2)
        batch_series = [series.get_series(x, y, z) for y, x, z in batch_points]
        res = pool.imap(_diff_ttest, batch_series)
        if res:
            result.extend(res)
            log.info("{} points processed.".format(len(result)))
        else:
            log.info("multiprocessing finished.")
            break
    pvalue_arr3d = np.array(result)
    pvalue_arr3d.reshape((y, x, z))
    return pvalue_arr3d
