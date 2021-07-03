# -*-coding:utf-8-*-

"""
程序可选菜单

@author Myles Yang
"""

import os
import sys

import win32con
import win32process

import const_config
import mylogger
import utils
from app_run_type import run_in_the_background, run_on_startup, run_in_the_console, create_startup_lnk
from configurator import get_pid_from_file, record_pid

_left = '\t' * 3


def __print_title():
    print('{}{}'.format(_left, '=' * 64))
    print('{0}‖ {1}随机桌面壁纸{1}‖ '.format(_left, ' ' * 24))
    print('{0}‖{1}让你的桌面壁纸就像一盒巧克力一样, 永远不知道下一颗是什么味道{1} ‖'.format(_left, ' ' * 0))
    print('{}{}'.format(_left, '=' * 64))


def __print_menu():
    __clear_console()
    print(end='\n\n')
    __print_title()
    print()
    print('{}【1】\t控制台启动'.format(_left), end='\n\n')
    print('{}【2】\t在后台启动'.format(_left), end='\n\n')
    print('{}【3】\t设置开机自启'.format(_left), end='\n\n')
    print('{}【4】\t取消开机自启'.format(_left), end='\n\n')
    print('{}【5】\t结束程序运行'.format(_left), end='\n\n')
    print('{}【6】\t在桌面创建快捷方式'.format(_left), end='\n\n')
    print('{}【7】\t关于本程序'.format(_left))
    print()
    menu_num = input('{}请输入相应数字执行操作: '.format(_left))
    try:
        menu_num = int(menu_num)
    except Exception:
        input('{}输入不合法，按任意键返回重做...'.format('\n' + _left))
        return __print_menu()

    return __menu_selected(menu_num)


def __menu_selected(menu_num: int):
    if menu_num == 1:
        __run_menu_1()
    elif menu_num == 2:
        __run_menu_2()
    elif menu_num == 3:
        __run_menu_3()
    elif menu_num == 4:
        __run_menu_4()
    elif menu_num == 5:
        __run_menu_5()
    elif menu_num == 6:
        __run_menu_6()
    elif menu_num == 7:
        __run_menu_7()
    else:
        input('{}输入不合法，按任意键返回重做...'.format('\n' + _left))
        return __print_menu()


def __run_menu_1():
    """ 控制台启动 """
    if not __is_app_running():
        __clear_console()
        mylogger.use_file_console_logger()
        run_in_the_console()


def __run_menu_2():
    """ 在后台启动 """
    if not __is_app_running():
        run_in_the_background()
        utils.create_dialog("程序已在后台启动...", const_config.dialog_title,
                            style=win32con.MB_OK, interval=5,
                            callback=lambda x: __print_menu())


def __run_menu_3():
    """ 设置开机自启 """
    pid = get_pid_from_file()
    if pid and win32process.GetProcessVersion(pid) > 0:
        create_startup_lnk()
    else:
        run_on_startup()
    utils.create_dialog('程序已后台启动，并设置开机自启', const_config.dialog_title,
                        style=win32con.MB_OK, interval=5,
                        callback=lambda x: __print_menu())


def __run_menu_4():
    """ 取消开机自启 """
    startup_path = utils.get_special_folders('Startup')
    if not startup_path:
        input('\n{}获取开机自启路径失败...'.format(_left))
        return __print_menu()
    fp, fn = os.path.split(sys.argv[0])
    mn, ext = os.path.splitext(fn)
    lnkname = mn + '.lnk'
    lnkpath = os.path.join(startup_path, lnkname)
    if os.path.isfile(lnkpath):
        os.remove(lnkpath)
        msg = '已取消开机自启！'
    else:
        msg = '未设置开机自启！'
    utils.create_dialog(msg, const_config.dialog_title,
                        style=win32con.MB_OK, interval=5,
                        callback=lambda x: __print_menu())


def __run_menu_5():
    """ 结束程序运行 """
    pid = get_pid_from_file()
    if pid and win32process.GetProcessVersion(pid) > 0:
        os.popen('TASKKILL /F /T /PID {}'.format(pid))
        record_pid(False)
        msg = '已结束程序的运行！'
    else:
        msg = '程序没有在运行！'
    utils.create_dialog(msg, const_config.dialog_title,
                        style=win32con.MB_OK, interval=5,
                        callback=lambda x: __print_menu())


def __run_menu_6():
    if utils.create_shortcut(sys.argv[0], 'shell:Desktop'):
        print("\n{}已在桌面创建快捷方式...".format(_left), )
    else:
        print("\n{}快捷方式创建失败...".format(_left))
    input('\n{}按任意键返回菜单...'.format(_left))
    return __print_menu()


def __run_menu_7():
    __clear_console()
    print(end='\n\n')
    __print_title()
    print()
    print('{}版本：1.2021.06.25'.format(_left), end='\n\n')
    print('{}作者：Myles Yang'.format(_left), end='\n\n')
    print('{}GitHub：https://github.com/snwjas/RandomDesktopBackground'.format(_left), end='\n\n')
    print('{}Gitee：https://gitee.com/snwjas/random-desktop-background'.format(_left), end='\n\n')
    input('\n{}按任意键返回菜单...'.format(_left))
    return __print_menu()


def __clear_console():
    os.system('cls')


def __is_app_running():
    pid = get_pid_from_file()
    # 程序在运行中
    if pid and win32process.GetProcessVersion(pid) > 0:
        utils.create_dialog("程序运行中，请勿重复运行！", const_config.dialog_title,
                            style=win32con.MB_ICONWARNING, interval=5,
                            callback=lambda x: __print_menu())
        return True
    return False


def main():
    os.popen('TITLE {}'.format(const_config.app_name))
    __print_menu()
