from os import listdir, curdir
from os.path import join, abspath, exists
from itertools import product
from functools import wraps
import logging

from h5py import File
import nibabel as nib
import numpy as np
import joblib

from helpers import get_logger


log = get_logger(__name__)


CACHE = "__cache__"


class Series(object):
    """
    Time Series of fMRI images, store all pixels's data in a hdf5 file.
    """
    def __new__(cls, hdf5_path, *args, **kwargs):
        """
        If the hdf5 file exist, will load it,
        else will create a new hdf5 file, in this situation,
        need these arguments:
            :image_dir: path to directory which store hdr image files.
            NOTE: Images name's character order must same to time sequence order.
            :time_interval: time interval between two images, unit: 1 second
        """
        if not exists(hdf5_path):
            image_dir = kwargs['image_dir']
            time_interval = kwargs['time_interval']
            cls.create_from_hdr(image_dir, hdf5_path, time_interval)
        return super(Series, cls).__new__(cls)

    def __init__(self, hdf5_path, cachedir=CACHE, *args, **kwargs):
        """
        Load Series from hdf5 file.
        :hdf5_path: path to related hdf5 file.
        :cachedir: path to cache directory, default current dir.
        """
        self.h5dict = File(hdf5_path, 'r+')
        for k, v in self.h5dict.attrs.items():
            setattr(self, k, v)

        self.cachedir = cachedir

    def _memoize(self, func, verbose=0):
        '''
        helper method for memory cache.
        '''
        if not hasattr(self, '_mymem'):
            self._mymem = joblib.Memory(cachedir=self.cachedir)

        memoized_func = self._mymem.cache(func, verbose=verbose)
        memoized_func.__doc__ = func.__doc__

        return memoized_func

    def _get_series(self, x, y, z):
        """
        return the time series(numpy array) at the position (z, y, x)
        """
        if hasattr(self, 'start') and hasattr(self, 'end'):
            s, e = self.start, self.end
            times = self.h5dict['arr4d'][s:e, y, x, z]
        else:
            times = self.h5dict['arr4d'][:, y, x, z]
        return times

    def get_series(self, *args, **kwargs):
        """ cached method, cache mothod at first run """
        self.get_series = self._memoize(self._get_series)
        return self.get_series(*args, **kwargs)

    def _get_arr3d(self, t):
        """
        return the 3d(y, x, z) array at the time point t.
        """
        arr3d = self.h5dict['arr4d'][t, :, :, :] # (t, y, x, z)
        return arr3d

    def get_arr3d(self, *args, **kwargs):
        """ cached method, cache mothod at first run """
        self.get_arr3d = self._memoize(self._get_arr3d)
        return self.get_arr3d(*args, **kwargs)

    def _get_arr2d(self, t, k, axis='xy'):
        """
        return 2d array at the time point t.
        :t: (int) time point of 2d array
        :k: (int) index of another dimension, e.g. axis == 'xy', k will means index of 'z' axis
        :axis: (str) the axis of 2d array. like: 'xy'(default), 'yz', 'xz'
        """
        arr3d = self.get_arr3d(t) # (t, y, x, z)
        assert axis in ('xy', 'yz', 'xz')
        if axis == 'xy':
            # k -> z
            arr2d = arr3d[:, :, k]
        elif axis == 'yz':
            # k -> x
            arr2d = arr3d[:, k, :]
        else: # 'xz'
            # k -> y
            arr2d = arr3d[k, :, :]
        return arr2d

    def get_arr2d(self, *args, **kwargs):
        """ cached method, cache mothod at first run """
        self.get_arr2d = self._memoize(self._get_arr2d)
        return self.get_arr2d(*args, **kwargs)

    def set_break_point(self, time):
        """
        set break point(the image index number when event occur)
        :time: time point when event occur, unit: second
        """
        assert 0 <= time <= self.n_images * self.time_interval
        self.break_point = int(time / self.time_interval)

    def set_range(self, start, end):
        """
        Set start and end position, for take subset of series.
        NOTE: after this method run, the behavior of `get_series` will change.
              `get_serirs` will return time_serirs[start:end]
        :start: (int) start position of time series
        :end: (int) end position of time series
        """
        self._mymem.clear()
        self.start = start
        self.end = end

    def call_simu(self, algorithm, *args, **kwargs):
        """
        Call simulation region, store result in the dict: self.simu_results
        :algorithm: the name of simulation calling method
        """
        import simucaller.call_simu as call_simu
        if not hasattr(self, 'simu_results'):
            self.simu_results = {}
        alg = getattr(call_simu, algorithm)
        result = alg(*args, **kwargs)
        self.simu_results.setdefault(algorithm, [])
        self.simu_results[algorithm].append(result)

    def save_simu_result(self):
        """
        Save simulation region call result to related hdf5 file.
        """
        pass

    def load_simu_result(self, algorithm, index):
        """
        Load simulation region call result from hdf5 file.
        :algorithm: result's calling method.
        :index: (int) index number of result.
        """
        result = self.h5dict['simulation_call_result'][algorithm][str(index)][...]
        return result

    @classmethod
    def create_from_hdr(cls, image_dir, hdf5_path, time_interval):
        """
        Create hdf5 file from hdr images.
        NOTE: Images name's character order must same to time sequence order.

        :time_interval: time interval between two images, unit: 1 second
        """
        img_files = [i for i in listdir(image_dir) if i.endswith('.hdr')]
        img_files.sort(key=lambda i: i.split('.')[0])
        img_files = [join(image_dir, i) for i in img_files]

        load_img = lambda f: nib.load(f).get_data()
        log.info("loading hdr images ...")
        imgs = [load_img(i) for i in img_files]
        n_images = len(imgs)
        log.info("{} hdr images loaded.".format(n_images))

        # check images shape, all images must in sam shape
        shape = y, x, z = imgs[0].shape
        log.info("image shape: {}".format(shape))
        for i, img in enumerate(imgs):
            assert img.shape == shape, \
                "Image {} expect in shape {} but get shape {}".format(
                    img_files[i], img.shape, shape
                )

        arr4d = np.array(imgs) # shape: (t, y, x, z)
        log.debug(arr4d[arr4d != 0])

        # store data
        h5dict = File(hdf5_path, 'w')
        log.info("hdf5 file created at {}".format(hdf5_path))
        h5dict.create_dataset('arr4d', shape=arr4d.shape)
        h5dict['arr4d'][...] = arr4d
        log.info("time series dataset shape {}".format(arr4d.shape))

        # store meta data
        h5dict.attrs['n_images'] = n_images
        h5dict.attrs['shape'] = arr4d.shape
        h5dict.attrs['time_interval'] = float(time_interval)
        log.info("time interval: {}s".format(time_interval))
        h5dict.close() # close hdf5 file
        log.info("Series hdf5 file creating process finished")
