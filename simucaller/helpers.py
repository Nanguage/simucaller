import itertools
from functools import wraps
import inspect
import logging

def get_logger(name):
    """
    helper function for generate logger.
    """
    logger = logging.getLogger(name)
    h = logging.NullHandler()
    logger.addHandler(h)
    return logger

def include_doc(child_funcs, tab=True):
    """
    Add child_func's doc to func.

    :child_funcs: (list) child function list
    :tab: if True, will add tab before each line of child_func's doc
    """
    def decorator(func):
        for child_func in child_funcs:
            # add child_func's header to parent's doc
            func.__doc__ += "\n"
            func.__doc__ += "{}:\n".format(child_func.__name__)
            for line in child_func.__doc__:
                if tab:
                    func.__doc__ += "\t"
                func.__doc__ += line + "\n"
        return func
    return decorator

def log_argumrnts(logger):
    """
    log func's arguments before call.
    """
    def decorator(func):
        @wraps
        def wraped_func(*args, **kwargs):
            args = inspect.getcallargs(func, *args, **kwargs)
            msg = "call `{}` with arguments: {}".format(func.__name__, args)
            logger.info(msg)
            return func(*args, **kwargs)
        return wraped_func
    return decorator

def grouper(iterable, n):
    """
    get a chuncked iterator, chunk size:n
    """
    it = iter(iterable)
    while True:
       chunk = tuple(itertools.islice(it, n))
       if not chunk:
           return
       yield chunk