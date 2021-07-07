# -*-coding:utf-8-*-

"""
工具模块

@author Myles Yang
"""
import imghdr
import os
import re
import threading
import time

import pythoncom
import win32api
import win32com.client as win32com_client
import win32con
import win32gui

import mylogger

log = mylogger.default_loguru

# 对每次创建对话框进行计数，方便查找同名对话框的句柄
__show_dialog_times = 0


def is_background_valid(bg_abs_path: str):
    """
    判断壁纸是否可用（是否是允许的图片类型）

    :param bg_abs_path: 壁纸绝对位置
    :return: True-可用; False-不可用
    """
    if os.path.isfile(bg_abs_path):
        # 这东西有时正常格式图片会检测不出来
        file_ext = imghdr.what(bg_abs_path)
        # 图片后缀，这些基本够用了，实际在设置时windows会将图片转换为jpg格式
        # 这些后缀的图片经过测试都能设置为桌面背景
        valid_img_ext_patn = 'png|jp[e]{0,1}g|gif|bmp|tif'
        if file_ext and re.match(valid_img_ext_patn, file_ext):
            return True
    return False


def set_background_fit(wallpaper_style=0, tile_wallpaper=0):
    """
    设置桌面背景契合度（交给用户自行设置）
    """

    # 打开指定注册表路径
    sub_reg_path = "Control Panel\\Desktop"
    reg_key = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, sub_reg_path, 0, win32con.KEY_SET_VALUE)
    # WallpaperStyle:2拉伸,6适应,10填充,22跨区，其他0
    win32api.RegSetValueEx(reg_key, "WallpaperStyle", 0, win32con.REG_SZ, str(wallpaper_style))
    # TileWallpaper：1平铺，居中0，其他0
    win32api.RegSetValueEx(reg_key, "TileWallpaper", 0, win32con.REG_SZ, str(tile_wallpaper))
    win32api.RegCloseKey(reg_key)


def get_shortcut(shortcut):
    """
    获取快捷方式
    :param shortcut: 快捷方式对象或路径
    :return: 快捷方式指向的文件绝对路径
    """
    if not is_main_thread():
        pythoncom.CoInitialize()
    try:
        ws = win32com_client.Dispatch("WScript.Shell")
        return ws.CreateShortCut(shortcut).Targetpath
    except Exception as e:
        log.error("获取快捷方式[{}]指向目标失败：{}".format(shortcut, e))
    finally:
        if not is_main_thread():
            pythoncom.CoUninitialize()
    return None


def create_shortcut(filename: str, lnkname: str = None, args: str = None, style: int = None):
    """
    创建快捷方式
    :param filename: 目标文件名（需含路径）
    :param lnkname: 快捷方式名，可以是路径，也可以的包含路径的文件名（文件名需含后缀.lnk），
                    还可以是windows特殊路径，它必须以shell:开头，如shell:desktop表示桌面路径
    :param args: 启动程序的参数
    :param style: 窗口样式，1.Normal window普通窗口,3.Maximized最大化窗口,7.Minimized最小化
    :return: 快捷方式对象(快捷方式路径)
    """
    target_path = os.path.abspath(filename)

    def get_lnkname():
        fp, fn = os.path.split(target_path)
        mn, ext = os.path.splitext(fn)
        return mn + '.lnk'

    if not lnkname:
        lnkname = get_lnkname()
    else:
        if os.path.isdir(lnkname):
            lnkname = os.path.join(lnkname, get_lnkname())
        else:
            if lnkname.lower().startswith('shell:'):
                spec_dir = get_special_folders(lnkname[6:])
                if spec_dir:
                    lnkname = os.path.join(spec_dir, get_lnkname())

    if not is_main_thread():
        pythoncom.CoInitialize()
    try:
        ws = win32com_client.Dispatch("WScript.Shell")
        shortcut = ws.CreateShortCut(lnkname)
        shortcut.TargetPath = target_path
        shortcut.WorkingDirectory = os.path.split(target_path)[0]
        shortcut.Arguments = args.strip() if args else ''
        shortcut.WindowStyle = style if (style and style in [1, 3, 7]) else 1
        shortcut.Save()
        return shortcut
    except Exception as e:
        log.error("创建程序[{}]快捷方式失败：{}".format(target_path, e))
    finally:
        if not is_main_thread():
            pythoncom.CoUninitialize()
    return None


def get_special_folders(name: str):
    """
    获取 windows 特定目录路径
    :param name: windows目录特定值名称，如Desktop、Startup...
    """
    if not is_main_thread():
        pythoncom.CoInitialize()
    try:
        ws = win32com_client.Dispatch("WScript.Shell")
        return ws.SpecialFolders(name)
    except Exception as e:
        log.error("获取 windows 特定目录路径[{}]失败：{}".format(name, e))
    finally:
        if not is_main_thread():
            pythoncom.CoUninitialize()

    return None


def locate_path(path: str):
    """
    打开资源管理器定位到相应路径
    """
    if path and os.path.exists(path):
        os.popen('explorer /e,/select,{}'.format(path))


def run_in_background(runnable_target):
    """
    后台运行目标程序
    """
    if not is_main_thread():
        pythoncom.CoInitialize()
    try:
        ws = win32com_client.Dispatch("WScript.Shell")
        res = ws.Run(runnable_target, 0)
        return True, res
    except Exception as e:
        log.error("设置目标程序后台启动失败：{}".format(e))
        return False, str(e)
    finally:
        if not is_main_thread():
            pythoncom.CoUninitialize()


def create_dialog(message: str, title: str, style: int = win32con.MB_OK,
                  block: bool = None, interval: float = 0, callback=None):
    """
    创建一个 Windows 对话框，支持同步异步和自动关闭

    值得注意的是，对于多选一没有关闭/取消功能的对话框，是不会自动关闭的，
    例如win32con.MB_YESNO、win32con.MB_ABORTRETRYIGNORE等等。

    :param message: 对话框消息内容
    :param title: 对话框标题
    :param style: 对话框类型
    :param block: 对话框是否阻塞调用线程，默认值取决于interval<=0，为Ture不会自动关闭，意味着阻塞调用线程
    :param interval: 对话框自动关闭秒数
    :param callback: 对话框关闭时的回调函数，含一参数为对话框关闭结果(按下的按钮值)
    :return: 当对话框为非阻塞时，无返回值(None)，否则，对话框阻塞当前线程直到返回,值为按下的按钮值
    """

    global __show_dialog_times
    __show_dialog_times += 1

    title = '{} [{}]'.format(title, __show_dialog_times)

    def cb(res):
        if callback and callable(callback):
            callback(res)

    def set_active():
        times_retry = 10
        while times_retry > 0:
            time.sleep(0.1)
            hwnd = win32gui.FindWindow(None, title)
            if hwnd:
                try:
                    win32gui.SetForegroundWindow(hwnd)
                finally:
                    return
            times_retry -= 1

    def show(timer: threading.Timer):
        threading.Thread(target=set_active).start()
        btn_val = win32api.MessageBox(0, message, title, style)
        if timer and timer.is_alive():
            timer.cancel()
        cb(btn_val)
        return btn_val

    def close():
        hwnd = win32gui.FindWindow(None, title)
        if hwnd:
            try:
                # PostMessage 异步，SendMessage 同步
                # win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                # win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                # win32gui.EndDialog(hwnd, None)
                # 需要注意的是倒数第二个参数，指定如何发送消息
                # http://timgolden.me.uk/pywin32-docs/win32gui__SendMessageTimeout_meth.html
                # https://blog.csdn.net/hellokandy/article/details/53408799
                # win32gui.SendMessageTimeout(hwnd, win32con.WM_CLOSE, 0, 0, win32con.SMTO_BLOCK, 1000)
                win32gui.EndDialog(hwnd, win32con.IDCLOSE)
            except Exception as e:
                log.error("对话框[{}]关闭错误：{}".format(title, e))

    block = block if (block is not None) else interval <= 0

    timer = None
    if interval > 0:
        timer = threading.Timer(interval, close)
        timer.start()

    if block:
        return show(timer)
    else:
        threading.Thread(target=lambda: show(timer)).start()


def list_deduplication(li: list):
    """
    列表去重
    """
    if not li:
        return list()
    res = list(set(li))
    res.sort(key=li.index)
    return res


def is_main_thread():
    """
    检测当前线程是否为主线程
    """
    return threading.current_thread() is threading.main_thread()


def is_lock_workstation():
    """
    判断Windows是否处于锁屏状态
    目前暂时无法做到检测屏幕关屏状态
    """
    hwnd = win32gui.GetForegroundWindow()
    return hwnd <= 0
