# -*-coding:utf-8-*-

"""
自定义简单的循环单任务定时器

@author Myles Yang
"""

from threading import Timer


class SimpleTaskTimer(object):
    """
    简单的循环单任务定时器，非阻塞当前线程

    @author Myles Yang
    """

    def __init__(self):
        self.__timer: Timer = None
        self.__seconds = 0
        self.__action = None
        self.__args = None
        self.__kwargs = None

    def run(self, seconds: int, action, args=None, kwargs=None):
        """
        执行循环定时任务

        :param seconds: 任务执行间隔，单位秒
        :param action: 任务函数
        :param args: 函数参数
        """
        if not callable(action):
            raise AttributeError("参数action非法，请传入函数变量")

        if self.is_running():
            print("已有任务在执行，请取消后再操作")
            return

        self.__action = action
        self.__seconds = seconds
        self.__args = args if args is not None else []
        self.__kwargs = kwargs if kwargs is not None else {}

        self.__run_action()

    def __run_action(self):
        self.__timer = Timer(self.__seconds, self.__hook, self.__args, self.__kwargs)
        self.__timer.start()

    def __hook(self, *args, **kwargs):
        self.__action(*args, **kwargs)
        self.__run_action()

    def is_running(self):
        """
        判断任务是否在执行
        """
        return self.__timer and self.__timer.is_alive()

    def cancel(self):
        """
        取消循环定时任务
        """
        if self.is_running():
            self.__timer.cancel()
            self.__timer = None
