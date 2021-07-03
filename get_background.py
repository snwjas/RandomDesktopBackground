# -*-coding:utf-8-*-

import configparser
import json
import os
import random
import shutil
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures._base import Future

import requests
import win32con

import configurator
import const_config
import mylogger
import utils
from set_background import SetBackgroundTask

log = mylogger.default_loguru

_get_random_bg_urls_max_failures = 10

request_api = 'https://wallhaven.cc/api/v1/search'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6776.400 QQBrowser/10.3.2577.400'
}


def get_proxies():
    return urllib.request.getproxies()


class GetBackgroundTask(object):
    """
    获取随机壁纸

    @author Myles Yang
    """

    def __init__(self, config: configparser.RawConfigParser):
        # 下载的壁纸任务
        # 总任务数量
        self.taskCount = 0
        # 已完成的任务数量（不论成功失败）
        self.taskDoneCount = 0
        # 已完成且成功的任务数量
        self.taskDoneSucceedCount = 0

        # 记录获取壁纸链接列表失败的次数
        self.get_random_bg_urls_failures = 0

        # 下载任务开始前，保存旧数据，任务完成后删除
        self.old_bg_abspaths = []

        self.config = config
        self.task: SetBackgroundTask = None

    def init_task(self, task: SetBackgroundTask):
        """
        初始化设置壁纸任务对象
        """
        self.task = task

    def run(self):
        """
        拉取壁纸
        :return
        """
        if not self.task:
            raise AttributeError("SetBackgroundTask对象未初始化，请执行init_task方法")

        if self.taskCount > 0:
            log.info('后台正在拉取壁纸...请等待任务完成在执行此操作！')
            utils.create_dialog('后台正在拉取壁纸...\n\n请等待任务完成在执行此操作!', const_config.dialog_title,
                                interval=5, style=win32con.MB_ICONWARNING)
            return False

        log.info('正在拉取新的随机壁纸...')
        log.info('线程数量: {}，下载每个壁纸前随机暂停时间在{}之间'.format(
            configurator.get_dwn_threads(self.config),
            configurator.get_random_sleep(self.config)
        ))
        self.taskCount = 1

        # 保存原来的壁纸的路径
        self.old_bg_abspaths = configurator.get_bg_abspaths()
        # 拉取壁纸
        bg_urls = self.get_random_bg_urls()
        if bg_urls:
            log.info('随机壁纸链接列表拉取成功: {}'.format(bg_urls))
            self.taskCount = len(bg_urls)
            threading.Thread(target=lambda: self.parallel_dwn_bg(bg_urls)).start()
            return True
        else:
            self.taskCount = 0

        return False

    def get_random_bg_urls(self):
        """
        获取随机壁纸链接列表

        :param config: configparser.ConfigParser 配置文件对象
        :return: 壁纸链接列表
        """
        proxies = get_proxies()
        if proxies:
            log.info('使用代理服务器配置拉取壁纸: {}'.format(proxies))

        params = configurator.get_request_params(self.config)
        bg_url_list = []
        resp = None
        try:
            resp = requests.get(request_api, params, headers=headers, proxies=proxies, timeout=(5, 60))
        except Exception as e:
            log.error('获取壁纸链接列表超时: {}'.format(e))

        if resp and resp.status_code == 200:
            data = None
            try:
                data = json.loads(resp.text)
            except Exception as e:
                log.error('JSON数据解析错误: {}'.format(e))
            if data:
                for item in data.get('data'):
                    bg_url = item.get('path')
                    if bg_url:
                        bg_url_list.append(bg_url)
        if resp and resp.status_code != 200:
            log.error("获取壁纸链接列表失败，状态码: {}，URL: {}，错误: {}"
                      .format(resp.status_code, resp.url, resp.text))

        if not bg_url_list:
            self.get_random_bg_urls_failures += 1
            if self.get_random_bg_urls_failures > _get_random_bg_urls_max_failures:
                btn_val = utils.create_dialog("拉取壁纸列表多次失败，将无法正常切换桌面背景！\n\n"
                                              "请检查配置文件或系统代理服务器配置是否异常！\n\n"
                                              "点击[是/Yes]退出程序，点击[否/No]继续运行！",
                                              const_config.dialog_title,
                                              style=win32con.MB_YESNO)
                if btn_val == win32con.IDYES:
                    os._exit(1)
                else:
                    self.get_random_bg_urls_failures = 0
                    self.task.set_current(0)
        else:
            self.get_random_bg_urls_failures = 0

        return bg_url_list

    def dwn_bg(self, bg_url, filename: str = None):
        """
        下载单个壁纸到 wallpapers 目录中

        :param bg_url: 壁纸链接
        :param filename: 壁纸文件名
        :return: 下载成功返回壁纸保存的绝对位置，否则为None
        """
        rndsleep = configurator.get_random_sleep(self.config)
        time.sleep(random.uniform(rndsleep[0], rndsleep[1]))

        res_bg_abspath = None
        try:
            resp = requests.get(bg_url, headers=headers, proxies=get_proxies(), timeout=(5, 120))
        except:
            log.error("下载壁纸超时: {}".format(bg_url))
            return res_bg_abspath

        if resp.status_code == 200:
            bg_srcpath = const_config.bg_srcpath
            if not os.path.isdir(bg_srcpath):
                os.makedirs(bg_srcpath)
            filename = filename if filename else os.path.basename(bg_url)
            with open(os.path.join(bg_srcpath, filename), 'wb') as bgfile:
                bgfile.write(resp.content)
            bg_abspath = os.path.abspath(bg_srcpath)
            res_bg_abspath = os.path.join(bg_abspath, filename)
        else:
            log.error("下载壁纸失败，状态码: {}，URL: {}，错误: {}"
                      .format(resp.status_code, resp.url, resp.text))

        return res_bg_abspath

    def parallel_dwn_bg(self, bg_urls):
        """
        多线程下载壁纸到 wallpapers 文件夹下

        对于限流的网站，降低线程数，增加下载图片前的延时，以提高下载成功率

        :param bg_urls: 壁纸链接列表
        """
        threads = configurator.get_dwn_threads(self.config)
        with ThreadPoolExecutor(max_workers=threads, thread_name_prefix='DwnBg') as pool:
            for bg_url in bg_urls:
                future = pool.submit(self.dwn_bg, bg_url)
                future.add_done_callback(self.bg_dwned_callback)
            pool.shutdown(wait=True)

    def bg_dwned_callback(self, future: Future):
        """
        重要函数，图片下载完毕时的回调函数
        :param future: concurrent.futures._base.Future()
        """
        self.taskDoneCount += 1

        bg_abspath = future.result()
        if bg_abspath:
            bg_abspath = str(bg_abspath)
            self.taskDoneSucceedCount += 1
            self.task.add_bg_path(bg_abspath)
            # 下载完成一张图片马上更新桌面背景
            if self.taskDoneSucceedCount == 1:
                self.task.set_background(bg_abspath)

        # 任务完成
        if self.taskDoneCount >= self.taskCount:
            log.info('壁纸拉取完毕，任务总数{}，成功{}'.format(self.taskCount, self.taskDoneSucceedCount))
            if self.taskDoneSucceedCount > 0:
                # 保留
                if configurator.is_retain_bg_files(self.config):
                    dirname = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                    for path in self.old_bg_abspaths:
                        dir_path = os.path.join(const_config.bg_srcpath, dirname)
                        os.makedirs(dir_path, exist_ok=True)
                        if os.path.isfile(path):
                            shutil.move(path, dir_path)
                else:  # 删除
                    for path in self.old_bg_abspaths:
                        if os.path.isfile(path):
                            os.remove(path)
                self.old_bg_abspaths = []
            # 重置任务计数
            self.taskCount = self.taskDoneCount = self.taskDoneSucceedCount = 0
