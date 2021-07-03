# -*-coding:utf-8-*-

"""
程序启动参数定义、获取与解析

@author Myles Yang
"""

import argparse

import const_config

""" 设置命令参数时的KEY """
# 程序运行方式
ARG_RUN = '--run'
# 程序日志记录方式
ARG_LOG = '--log'
# 创建程序快捷方式
ARG_LNK = '--lnk'

""" 获取命令参数值时的KEY """
ARG_KEY_RUN = 'RUNTYPE'
ARG_KEY_LOG = 'LOGTYPE'
ARG_KEY_LNK = 'LNKPATH'

""" --run 命令参数选项 """
# 控制台启动
ARG_RUN_TYPE_CONSOLE = 'console'
# 控制台后台启动
ARG_RUN_TYPE_BACKGROUND = 'background'
# 开机自启，控制台后台启动
ARG_RUN_TYPE_POWERBOOT = 'powerboot'

""" --log 命令参数选项 """
# 文件方式记录运行日志
ARG_LOG_TYPE_FILE = 'file'
# 控制台打印方式记录运行日志
ARG_LOG_TYPE_CONSOLE = 'console'
# 文件和控制台打印方式记录运行日志
ARG_LOG_TYPE_BOTH = 'both'
# 禁用日志记录
ARG_LOG_TYPE_NONE = 'none'

"""
定义命令行输入参数
"""
parser = argparse.ArgumentParser(
    prog=const_config.app_name,
    description='随机桌面壁纸命令行参数',
)

parser.add_argument('-r', '--run',
                    help='指定程序的运行方式',
                    type=str,
                    choices=['console', 'background', 'powerboot'],
                    dest='RUNTYPE'
                    )

parser.add_argument('-l', '--log',
                    help='指定运行日志记录的方式',
                    type=str,
                    choices=['file', 'console', 'both', 'none'],
                    dest='LOGTYPE'
                    )

parser.add_argument('-s', '--lnk',
                    help='根据给的路径创建程序的快捷方式',
                    type=str,
                    nargs='*',
                    dest='LNKPATH'
                    )

arg_dict = vars(parser.parse_args())
