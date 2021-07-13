# -*-coding:utf-8-*-

"""
程序的运行方式

@author Myles.yang
"""

import os
import sys

import win32con

import args_definition
import configurator
import const_config
import utils
from get_background import GetBackgroundTask
from set_background import SetBackgroundTask


def run_in_the_console():
    """
    以控制台程序方式运行，日志会打印在控制台
    """
    config = configurator.parse_config()
    bg_abspath_list = configurator.get_bg_abspaths()

    # 这样写SetBackgroundTask传入get_bg_func，与GetBackgroundTask.init_task
    # 的原因是为了避免循环依赖，是代码设计上的缺陷

    gtask = GetBackgroundTask(config)
    stask = SetBackgroundTask(config, bg_abspath_list, gtask.run)

    gtask.init_task(stask)

    stask.run()

    """ 执行到这里程序已经跑起来了 """

    # 记录运行中程序的PID
    configurator.record_pid()


def run_in_the_background(log_type: str = None):
    """
    以控制台程序方式在后台运行
    """
    app_path = os.path.abspath(sys.argv[0])
    # 值得注意的是，这里进入后台运行的方式应该是CONSOLE，因为是以控制台的方式后台运行的，
    # 如果为 BACKGROUND 的话，会造成递归调用，不断循环启动应用，主进程PID不断改变，无法停止应用。
    # main -> background -> 后台运行 -> main -> 开始循环递归
    args = ' {} {} {} {}'.format(args_definition.ARG_RUN, args_definition.ARG_RUN_TYPE_CONSOLE,
                                 args_definition.ARG_LOG, log_type if log_type else args_definition.ARG_LOG_TYPE_FILE
                                 )

    succeed, msg = utils.run_in_background(app_path, args)
    if not succeed:
        utils.create_dialog_w("后台启动程序失败:\n\n{}".format(msg),
                              const_config.dialog_title, style=win32con.MB_ICONWARNING)
    return succeed

    # run_in_the_console()
    # ct = win32api.GetConsoleTitle()
    # hd = win32gui.FindWindow(None, ct)
    # win32gui.ShowWindow(hd, win32con.SW_HIDE)


def run_on_startup(log_type: str = None):
    """
    开机时启动，默认以后台方式运行程序
    """
    # 创建快捷方式到用户开机启动目录: shell:startup
    create_startup_lnk(log_type)
    # 后台运行
    return run_in_the_background(log_type)


def create_startup_lnk(log_type: str = None):
    """
    # 创建快捷方式到用户开机启动目录: shell:startup
    """
    app_path = os.path.abspath(sys.argv[0])
    startup_path = utils.get_special_folders('Startup')
    args = '{} {} {} {}'.format(args_definition.ARG_RUN, args_definition.ARG_RUN_TYPE_BACKGROUND,
                                args_definition.ARG_LOG, log_type if log_type else
                                args_definition.ARG_LOG_TYPE_FILE,
                                )
    if startup_path:
        return utils.create_shortcut(app_path, lnkname=startup_path, args=args, style=7)
    utils.create_dialog_w("设置开机自启失败", const_config.dialog_title, interval=5, style=win32con.MB_ICONWARNING)
