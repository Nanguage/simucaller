import logging

def get_logger(name):
    """
    helper function for generate logger.
    """
    logger = logging.getLogger(name)
    h = logging.NullHandler()
    logger.addHandler(h)
    return logger