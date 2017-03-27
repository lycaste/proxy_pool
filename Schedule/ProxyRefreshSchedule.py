# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File Name：     ProxyRefreshSchedule.py  
   Description :  代理定时刷新
   Author :       JHao
   date：          2016/12/4
-------------------------------------------------
   Change Activity:
                   2016/12/4: 代理定时刷新
                   2017/03/06: 使用LogHandler添加日志
-------------------------------------------------
"""

import sys
import time
import requests
import json
from multiprocessing import Process
from apscheduler.schedulers.blocking import BlockingScheduler

sys.path.append('../')

from Manager.ProxyManager import ProxyManager
from Util.LogHandler import LogHandler


__author__ = 'JHao'


url = 'http://ditu.amap.com/service/poiInfo?query_type=RQBXY&pagesize=20000&pagenum=&qii=true&cluster_state=5&need_utd=true&utd_sceneid=1000&div=PC1000&addr_poi_merge=true&is_classify=true&zoom=15&longitude=121.319963&latitude=31.194223&range=1000&city=310000&keywords=%E7%BE%8E%E9%A3%9F'
class ProxyRefreshSchedule(ProxyManager):
    """
    代理定时刷新
    """

    def __init__(self):
        ProxyManager.__init__(self)
        self.log = LogHandler('refresh_schedule')

    def valid_proxy(self):
        """
        valid_proxy
        :return:
        """
        self.db.changeTable(self.raw_proxy_queue)
        raw_proxy = self.db.pop()
        self.log.info('%s start valid proxy' % time.ctime())
        while raw_proxy:
            proxies = {"http": "http://{proxy}".format(proxy=raw_proxy),
                       "https": "https://{proxy}".format(proxy=raw_proxy)}
            try:
                # 超过30秒的代理就不要了
                r = requests.get(url, proxies=proxies, timeout=10, verify=False)
                data = json.loads(r)
                print data
                if data.get('status') == '1':
                    self.db.changeTable(self.useful_proxy_queue)
                    self.db.put(raw_proxy)
                    self.log.debug('proxy: %s validation passes' % raw_proxy)
            except Exception, e:
                self.log.debug('proxy: %s validation fail' % raw_proxy)
                pass
            self.db.changeTable(self.raw_proxy_queue)
            raw_proxy = self.db.pop()
        self.log.info('%s valid proxy complete' % time.ctime())


def refresh_pool():
    pp = ProxyRefreshSchedule()
    pp.valid_proxy()


def main(process_num=10):
    p = ProxyRefreshSchedule()
    p.refresh()
    pl = []
    for num in range(process_num):
        proc = Process(target=refresh_pool, args=())
        pl.append(proc)

    for num in range(process_num):
        pl[num].start()

    for num in range(process_num):
        pl[num].join()


if __name__ == '__main__':
    main()
    sched = BlockingScheduler()
    sched.add_job(main, 'interval', minutes=10)
    sched.start()
