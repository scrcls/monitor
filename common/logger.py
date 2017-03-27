#! -*- coding:utf-8 -*-
import logging
import datetime
import logging.handlers

def setup_logger(name, logfile, tag = '', level = logging.INFO):
    logger = logging.getLogger(name)
    if tag:
        fmt = '%(asctime)s %(pathname)s/[line:%(lineno)d] %(levelname)s \n\t[{tag}]%(message)s'.format(tag = tag)
    else:
        fmt = '%(asctime)s %(pathname)s/[line:%(lineno)d] %(levelname)s \n\t%(message)s'
    formatter = logging.Formatter(
        fmt = fmt,
        datefmt = '%Y-%m-%d %H:%M:%S'
    )
    handler = logging.FileHandler(logfile)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
