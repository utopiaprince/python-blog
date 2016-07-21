import logging
import os

root_logger = ''


def log_init(log_file="log.log", level=logging.DEBUG):
    global root_logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    _sh = logging.StreamHandler()
    _sh.setLevel(level)
    _sh.setFormatter(formatter)
    root_logger.addHandler(_sh)
    print(root_logger)

    if(log_file is not None):
        _fh = logging.FileHandler(log_file)
        _fh.setLevel(level)
        _fh.setFormatter(formatter)
        root_logger.addHandler(_fh)


def log_debug(*args):
    global root_logger
    root_logger.debug(*args)


def log_info(*args):
    global root_logger
    root_logger.info(*args)


if __name__ == '__main__':
    log_init()
    log_info("this is a demo!")

