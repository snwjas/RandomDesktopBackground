# -*-coding:utf-8-*-

"""
相关配置配置读写解析

@author Myles Yang
"""

import configparser
import os
import re
import urllib.parse

import win32con

import const_config
import mylogger
import utils
from utils import create_dialog

log = mylogger.default_loguru


def get_bg_abspaths():
    """
    获取壁纸目录下的绝对路径列表

    不包括子目录

    :return: 壁纸绝对路径列表
    """
    bg_srcpath = const_config.bg_srcpath
    bg_paths = []
    if not os.path.isdir(bg_srcpath):
        return bg_paths

    bg_src_abspath = os.path.abspath(bg_srcpath)
    for df in os.listdir(bg_src_abspath):
        df_abspath = os.path.join(bg_src_abspath, df)
        if os.path.isfile(df_abspath):
            bg_paths.append(df_abspath)

    return bg_paths


def parse_config():
    """
    解析配置文件解析

    :return: configparser.RawConfigParser() 配置对象
    """
    config = configparser.RawConfigParser()
    config_srcpath = const_config.config_srcpath
    res = config.read([os.path.join(config_srcpath, 'config.ini')])
    if not res:
        # http://timgolden.me.uk/pywin32-docs/win32api__MessageBox_meth.html
        btn_val = create_dialog("配置文件丢失，是否使用默认配置启动？", const_config.dialog_title,
                                style=win32con.MB_YESNO)
        if btn_val != win32con.IDYES:
            os._exit(1)

        log.info("配置文件读取失败，加载默认配置")
        config = get_default_config()
        update_config_file(config)
    else:
        if not config.has_option('Api', 'url') and \
                not (config.has_section('Params') and not config.items('Params')):
            btn_val = create_dialog("配置文件未指定请求URL或参数，是否使用默认配置启动？", const_config.dialog_title,
                                    style=win32con.MB_YESNO)
            if btn_val != win32con.IDYES:
                os._exit(1)

            default_url = get_default_config().get('Api', 'url')
            __get_option(config, 'Api', 'url', default=default_url)

    return config


"""============================ [APi] ============================"""


def get_request_params(config: configparser.RawConfigParser = None):
    """
    从配置文件中获取请求参数
    :param config: configparser.RawConfigParser，如果为空则读取配置文件
    :return: 参数元组列表 list of (name, value) tuples
    """
    config = config if config else parse_config()
    if hasattr(config, 'req_params'):
        return config.req_params
    query = {}
    if config.has_option('Api', 'url'):
        url = config.get('Api', 'url')
        query = urllib.parse.urlsplit(url).query
        query = dict(urllib.parse.parse_qsl(query))

    params = {}
    if config.has_section('Params'):
        params = dict(config.items('Params'))

    # 合并两个字典，并移除空值
    dict_res = dict(query, **params)
    dict_res = {k: v for k, v in dict_res.items() if v}

    config.req_params = dict_res
    return dict_res


"""============================ [Task] ============================"""


def get_current(config: configparser.RawConfigParser = None):
    """
    获取配置中当前壁纸数组的下标
    :return: 值不存在或小于0，返回0
    """
    config = config if config else parse_config()
    return __get_int_option(config, 'Task', 'current', default=0, lt=0)


def set_current(current, config: configparser.RawConfigParser = None):
    """
    更新配置文件中当前壁纸数组的下标
    """
    config = config if config else parse_config()
    config.set('Task', 'current', str(current))
    update_config_file(config)


def get_seconds(config: configparser.RawConfigParser = None):
    """
    获取桌面背景更换的频率
    :return: 值不存在或小于10，返回300
    """
    config = config if config else parse_config()
    return __get_int_option(config, 'Task', 'seconds', default=300, lt=10)


def get_dwn_threads(config: configparser.RawConfigParser = None):
    """
    获取下载壁纸时的线程数
    """
    config = config if config else parse_config()
    default_threads = min(32, (os.cpu_count() or 1) + 4)
    return __get_int_option(config, 'Task', 'threads', default=2,
                            lt=1, lt_default=default_threads,
                            rt=32, rt_default=32)


def get_random_sleep(config: configparser.RawConfigParser = None):
    """
    获取在下载壁纸前的随机睡眠时间
    :return tuple: 返回两个元素的元组，生成两个数间的随机值
    """
    config = config if config else parse_config()
    if hasattr(config, 'rndsleep'):
        return config.rndsleep
    str_vals = __get_option(config, 'Task', 'rndsleep')
    rnd_vals = __get_multivalued_option(str_vals, ',', opt_type=float)

    need_update = False
    # 数据错误，返回默认值
    if not rnd_vals or len(rnd_vals) != 2:
        str_vals = get_default_config().get('Task', 'rndsleep')
        rnd_vals = __get_multivalued_option(str_vals, ',', opt_type=float)
        need_update = True

    # 检验每个值是否小于0
    for i in range(len(rnd_vals)):
        if rnd_vals[i] < 0:
            rnd_vals[i] = 0.0
            need_update = True

    # 判断两个值大小是否反了
    if rnd_vals[0] > rnd_vals[1]:
        tmp = rnd_vals[1]
        rnd_vals[1] = rnd_vals[0]
        rnd_vals[0] = tmp
        need_update = True
    if need_update:
        config.set('Task', 'rndsleep', '{},{}'.format(rnd_vals[0], rnd_vals[1]))
        update_config_file(config)

    config.rndsleep = tuple(rnd_vals)
    return config.rndsleep


def is_retain_bg_files(config: configparser.RawConfigParser = None):
    """
    在拉取新的壁纸前，是否删除旧的壁纸
    """
    return __get_bool_option(config, 'Task', 'retainbgs')


"""============================ [Hotkey] ============================"""


def is_hotkey_enabled(config: configparser.RawConfigParser):
    """
    是否启用热键
    """
    return __get_bool_option(config, 'Hotkey', 'enabled')


def get_hotkey_prev(config: configparser.RawConfigParser):
    """
    获取热键：上一个桌面背景
    """
    return __get_hotkey(config, 'Hotkey', 'hk_prev')


def get_hotkey_next(config: configparser.RawConfigParser):
    """
    获取热键：下一个桌面背景
    """
    return __get_hotkey(config, 'Hotkey', 'hk_next')


def get_hotkey_locate(config: configparser.RawConfigParser):
    """
    获取热键：定位到当前桌面背景文件
    """
    return __get_hotkey(config, 'Hotkey', 'hk_locate')


def __get_hotkey(config: configparser.RawConfigParser, section: str, option: str):
    """
    获取热键通用方法
    """
    if not (config or config.has_option(section, option)):
        return None
    hk_str = config.get(section, option)
    hk = __get_multivalued_option(hk_str, '+', opt_type=str)
    return utils.list_deduplication(hk)


"""============================  ============================"""


def __get_multivalued_option(opt_val: str, delimiter: str, opt_type: type = str):
    """
    获取多值配置项，通常由分隔符分割每一个值

    :param opt_val: 配置项字符值
    :param delimiter: 分割符
    :param opt_type: 配置的项每个值的数据类型，作为类型转换
    :return list: 配置项的每个值
    """
    if not (opt_val or delimiter):
        return []
    opt_vals = opt_val.split(delimiter)
    # 去除空白字符
    opt_vals = list(map(lambda s: s.strip(), opt_vals))
    # 去除空白项
    opt_vals = list(filter(lambda s: s, opt_vals))
    # 类型转换
    try:
        opt_vals = list(map(lambda s: opt_type(s), opt_vals))
    except:
        return []
    return opt_vals


def __get_int_option(config: configparser.RawConfigParser, section: str, option: str,
                     default: int = 0,
                     lt: int = None, lt_default: int = None,
                     rt: int = None, rt_default: int = None):
    """
    获取整数的配置项，
    注意：使用到默认值，必定会创建该值然后写入文件

    :param config: configparser.RawConfigParser 对象
    :param section: 配置项所属section
    :param option: 配置项key
    :param default: 解析失败或...时使用的默认值
    :param lt: if 配置值 < lt then (res = lt_default if lt_default else default)
    :param lt_default: 指定 lt 且不符合 lt 条件时返回的值
    :param rt: if 配置值 < rt then (res = rt_default if rt_default else default)
    :param rt_default: 指定 rt 且不符合 rt 条件时返回的值
    :return: 配置项的整数值
    """
    if not config.has_option(section, option):
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, option, str(default))
        update_config_file(config)
        return default

    try:
        seconds = config.getint(section, option)
    except:
        config.set(section, option, str(default))
        update_config_file(config)
        return default

    need_update = False
    if lt and seconds < lt:
        seconds = lt_default if (lt_default or lt_default == 0) else default
        need_update = True
    if rt and seconds > rt:
        seconds = rt_default if (rt_default or rt_default == 0) else default
        need_update = True
    if need_update:
        config.set(section, option, str(default))
        update_config_file(config)

    return seconds


def __get_option(config: configparser.RawConfigParser, section: str, option: str, default: str = ''):
    """
    获取配置项的值

    :param config: configparser.RawConfigParser 对象
    :param section: 配置项所属section
    :param option: 配置项key
    :param default: 获取失败时的默认值
    :return str: 配置项的值
    """
    if not config.has_option(section, option):
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, option, str(default))
        update_config_file(config)
        return default
    return config.get(section, option)


def __get_bool_option(config: configparser.RawConfigParser, section: str, option: str):
    """
    判断某项设置的波尔值

    :param config: configparser.RawConfigParser 对象
    :param section: 配置项所属section
    :param option: 配置项key
    :return: True or False
    """
    if (not config) or (not config.has_section(section)) \
            or (not config.has_option(section, option)):
        return False
    opt_val = config.get(section, option)
    if opt_val and not re.match('^(0|off|false)$', opt_val.lower()):
        return True
    return False


"""============================  ============================"""


def get_default_config():
    """
    读取默认配置并写入配置文件

    :return: configparser.RawConfigParser() 配置对象
    """
    config = configparser.RawConfigParser()
    # 配置默认属性
    config['Api'] = {
        'name': 'Default',
        'url': 'https://wallhaven.cc/api/v1/search'
    }
    config['Params'] = {
        'categories': '111',
        'purity': '100',
        'sorting': 'random',
        'order': 'desc',
    }
    config['Task'] = {
        'seconds': '600',
        'current': '0',
        'threads': '2',
        'rndsleep': '0.0,5.0',
        'retainbgs': '0',
    }
    config['Hotkey'] = {
        'enable': '1',
        'hk_prev': 'control+alt+left',
        'hk_next': 'control+alt+right',
        'hk_locate': 'control+alt+up',
    }
    config['App'] = {
        'version': '1.2021.06.25',
        'author': 'Myles Yang',
        'github': 'https://github.com/snwjas/RandomDesktopBackground',
        'gitee': 'https://gitee.com/snwjas/random-desktop-background',
    }
    update_config_file(config)
    return config


def update_config_file(config: configparser.RawConfigParser):
    """
    更新配置文件
    """
    if not config:
        return False
    config_srcpath = const_config.config_srcpath
    with open(os.path.join(config_srcpath, 'config.ini'), 'w') as configfile:
        config.write(configfile)
    return True


def record_pid(running: bool = True):
    """
    记录程序运行的PID
    """
    pid = os.getpid() if running else -1
    pid_path = os.path.join(const_config.pid_srcpath, 'pid')
    with open(pid_path, 'w') as f:
        f.write(str(pid))
        # 锁定PID文件
        # 共享锁:所有进程没有写访问权限，加锁进程也没有，但所有进程有读访问权限。
    return pid


def get_pid_from_file():
    """
    从文件获取PID
    :return int: 返回PID，获取失败返回None
    """
    pid_filepath = os.path.join(const_config.pid_srcpath, 'pid')
    if not os.path.isfile(pid_filepath):
        log.error('PID文件丢失，读取失败')
        return None
    try:
        with open(pid_filepath, 'r') as f:
            str_pid = f.read(20)
        str_pid = str_pid.strip()
        int_pid = int(str_pid)
    except Exception as e:
        log.error('读取PID失败: {}'.format(e))
        return None
    return int_pid
