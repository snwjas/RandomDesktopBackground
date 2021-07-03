# -*-coding:utf-8-*-

"""
程序启动入口
@author Myles Yang
"""

import sys

import app_menu
import args_definition
import mylogger
import utils
from app_run_type import run_in_the_background, run_on_startup, run_in_the_console


# 注册程序退出回调
# atexit.register大多时候是不会执行的，比如非正常crash（taskkill...），或通过os._exit()退出；
# 想到的另外一个方法是创建一个独立的进程（非子进程），对这个程序的运行进行循环检测，比如通过pid判断它是否存活，
# 可以使用 win32process.GetProcessVersion(pid:int) 进行检测，不存在的 pid 会返回 0；
# atexit.register(configurator.record_pid, False)


def main():
    # 获取启动参数
    arg_dict = args_definition.arg_dict
    # 创建程序快捷方式
    lnk_args = arg_dict.get(args_definition.ARG_KEY_LNK)
    if lnk_args or lnk_args == []:
        lnk_path = None if lnk_args == [] else lnk_args[0]
        args = ' '.join(lnk_args[1:])
        utils.create_shortcut(sys.argv[0], lnk_path, args)
    # 程序没指定运行参数，退出
    if not arg_dict.get(args_definition.ARG_KEY_RUN):
        # os._exit(-1)
        # 关闭日志
        mylogger.user_none()
        app_menu.main()
    else:
        # 首先确定运行日志记录方式
        log_type = arg_dict.get(args_definition.ARG_KEY_LOG)
        if log_type == args_definition.ARG_LOG_TYPE_FILE:  # 文件
            mylogger.use_file_logger()
            log_type = args_definition.ARG_LOG_TYPE_FILE
        elif log_type == args_definition.ARG_LOG_TYPE_CONSOLE:  # 控制台
            mylogger.use_console_logger()
            log_type = args_definition.ARG_LOG_TYPE_CONSOLE
        elif log_type == args_definition.ARG_LOG_TYPE_NONE:  # 禁用
            mylogger.user_none()
            log_type = args_definition.ARG_LOG_TYPE_NONE
        else:  # 文件和控制台
            mylogger.use_file_console_logger()
            log_type = args_definition.ARG_LOG_TYPE_BOTH
        # 最后确定程序运行方式
        run_type = arg_dict.get(args_definition.ARG_KEY_RUN)
        if run_type == args_definition.ARG_RUN_TYPE_BACKGROUND:  # 后台
            run_in_the_background(log_type)
        elif run_type == args_definition.ARG_RUN_TYPE_POWERBOOT:  # 开机自启，后台
            run_on_startup(log_type)
        else:  # 控制台
            run_in_the_console()


if __name__ == '__main__':
    main()
