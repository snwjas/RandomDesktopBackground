# -*-coding:utf-8-*-

"""
自定义日志解析

@author Myles Yang
"""

import os
import sys

from loguru import logger

import const_config

LOGGING_DEBUG = 10
LOGGING_INFO = 20
LOGGING_WARNING = 30
LOGGING_ERROR = 40
LOGGING_CRITICAL = 50

LOGURU_SUCCESS = 25

'''

import datetime
import logging
from logging import handlers


def get_logging_logger(level=LOGGING_INFO, name=None, console=True):
    """
    获取日志记录logger，默认记录在文件中，可同时开启控制台打印

    :param level: 日志类型
    :param name: 指定不同name区分日志记录器
    :param console: 是否同时在控制台打印
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 日志格式
    formatter = logging.Formatter('%(levelname)s\t%(asctime)s - %(name)s - %(filename)s - %(funcName)s - %(message)s')

    # 文件日志处理器
    log_srcpath = const_config.log_srcpath
    os.makedirs(log_srcpath, exist_ok=True)
    fh = handlers.TimedRotatingFileHandler(
        filename=os.path.join(log_srcpath, 'run.log.{}'.format(datetime.datetime.now().strftime('%Y-%m-%d'))),
        when='D',
        backupCount=30,
        encoding='UTF-8')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    fh.close()

    # 控制台
    if console:
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        ch.close()

    return logger


""" 打包exe后，日志会打印两次，原因未排除 """
default_logging = get_logging_logger()

'''

# 日志格式
__log_format = '{time:YYYY-MM-DD HH:mm:ss,SSS} | {level}\t | {file}:{function}:{line} | {message}'

logger.opt(lazy=True, colors=True)


def __add_file_handler():
    handler_id = logger.add(sink=os.path.join(const_config.log_srcpath, 'run.{time:YYYY-MM-DD}.log'),
                            format=__log_format,
                            rotation='1 day',
                            retention=30,
                            enqueue=True,
                            encoding='UTF-8'
                            )
    return handler_id


def __add_console_handler():
    info_handler_id = logger.add(sink=sys.stdout,
                                 level=LOGGING_INFO,
                                 # fg #097D80
                                 format='<g>' + __log_format + '</>',
                                 colorize=True,
                                 filter=lambda record: record["level"].name == "INFO"
                                 )
    err_handler_id = logger.add(sink=sys.stdout,
                                level=LOGGING_ERROR,
                                # fg #F56C6C
                                format='<r>' + __log_format + '</>',
                                colorize=True,
                                filter=lambda record: record["level"].name == "ERROR"
                                )
    return info_handler_id, err_handler_id


def use_file_console_logger():
    logger.remove(handler_id=None)
    __add_file_handler()
    __add_console_handler()
    return logger


def use_console_logger():
    logger.remove(handler_id=None)
    __add_console_handler()
    return logger


def use_file_logger():
    logger.remove(handler_id=None)
    __add_file_handler()
    return logger


def user_none():
    logger.remove(handler_id=None)
    return logger


default_loguru = use_file_console_logger()
