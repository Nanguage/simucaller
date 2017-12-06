import pytest

import os
from shutil import rmtree
from subprocess import check_call
import sys
sys.path.insert(0, "../")

from simucaller.series import Series
from simucaller.helpers import get_logger

import logging
logging.basicConfig(level=logging.DEBUG)
log = get_logger(__name__)

data_dir = "./data"

hdf5 = "./test.h5"
cache = "./.cache"

time_interval = 2
n_images = 350
shape = (64, 64, 9)


def test_Series():
    """ test Series object creation """
    # create from hdr image files
    Series(hdf5, image_dir=data_dir,
           time_interval=time_interval, cachedir=cache)
    # loading from hdf5 file
    Series(hdf5, cachedir=cache)

def test_get_series():
    """ test Series.get_series method """
    series = Series(hdf5, cachedir=cache)
    s = series.get_series(21, 21, 2)
    log.debug(s.shape)
    assert len(s) == n_images

def test_get_arr3d():
    """ test Series.get_arr3d method """
    series = Series(hdf5, cachedir=cache)
    arr = series.get_arr3d(100)
    log.debug(arr.shape)
    assert arr.shape == shape

def test_get_arr2d():
    """ Series.get_arr2d """
    series = Series(hdf5, cachedir=cache)
    arr2d = series.get_arr2d(100, 3, axis='xy')
    assert arr2d.shape == shape[0:2]
    arr2d = series.get_arr2d(100, 20, axis='yz')
    assert arr2d.shape == (shape[0], shape[2])
    arr2d = series.get_arr2d(100, 20, axis='xz')
    assert arr2d.shape == (shape[1], shape[2])

def test_set_break_points():
    """ Serirs.set_break_points """
    series = Series(hdf5, cachedir=cache)
    series.set_break_points((100, 110))
    log.debug(series.break_points)
    try:
        series.set_break_points(((n_images + 1), (n_images + 2)))
    except AssertionError as e:
        log.debug(e)

def test_set_simu_intervals():
    """ Series.set_simu_intervals """
    series = Series(hdf5, cachedir=cache)
    series.set_simu_intervals([(100, 110), (130, 140)])
    log.debug(series.simu_intervals)

def test_set_range():
    """ Series.set_range """
    series = Series(hdf5, cachedir=cache)
    assert len(series.get_series(20, 20, 1)) == n_images
    series.set_range(0, 150)
    assert len(series.get_series(20, 20, 1)) == 150

def test_call_simu():
    """
    Series.call_simu
    Series.save_simu
    """
    series = Series(hdf5, cachedir=cache)
    # test algorithm diff_ttest
    series.set_break_points((100, 110))
    series.call_simu('diff_ttest', 'call_0')
    series.save_simu_result('diff_ttest', 'call_0')
    # test algorithm ttest
    series.set_simu_intervals([(28 + i*40, 28 + i*40 + 10) for i in range(8)])
    series.call_simu('ttest', 'call_1')
    series.save_simu_result('ttest', 'call_1')

    # save attributes
    series.save_attr()

#def test_clean():
#    """ clean all intermedia files """
#    os.remove(hdf5)
#    rmtree(cache)