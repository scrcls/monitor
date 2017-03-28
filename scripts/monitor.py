#! -*- coding:utf-8 -*-
import importme

from common.logger import setup_logger
from common.utils import to_float

from bs4 import BeautifulSoup
import click
import datetime
import logging
import json
import re
import requests
import time

logger = setup_logger('monitor', 'monitor.log')
change_logger = setup_logger('change', 'change.log')

class Product(object):
    def __init__(self):
        self.id = None
        self.title = ''
        self.price = None
        self.yield_rate = None
        self.close_time = None
        self.expire_time = None

    def set_yield_rate(self, rate):
        self.yield_rate = rate
        if rate.find('%'):
            float_rate = to_float(rate.replace('%', ''))
            if float_rate:
                self.yield_rate = float_rate

    def __iter__(self):
        return iter([
            ('id', self.id),
            ('title', self.title),
            ('price', self.price),
            ('yield_rate', self.yield_rate),
            ('close_time', self.close_time),
            ('expire_time', self.expire_time),
        ])

    def __str__(self):
        info = u''
        for key, val in iter(self):
            info += u'%s: %s\n' % (key, val)
        return info.encode('utf-8')

class ProductChange(object):
    def __init__(self):
        self.product_id = None
        self.up_time = None
        self.down_time = None
        self.product = None

    def __iter__(self):
        return iter([
            ('up_time', self.up_time),
            ('down_time', self.down_time),
            ('product', dict(self.product) if self.product else None),
        ])


class BankFetcher(object):

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Cookie': 'Hm_lvt_9311ae0af3818e9231e72458be9cdbce=1490088074,1490088398,1490088508,1490088540; JSESSIONID=BZm1YZQFCm21p14fLSyyQJ0KhyGyXtQRwnGmgVC2bjTdTGCkSLTy!1102000751'
    }

    def __init__(self, cookie):
        pass
        #self.HEADERS['Cookie'] = cookie

    def fetch(self, page = 1):
        url = 'https://3g.cib.com.cn/app/20173.html'
        data = {
            'viewflag': 0,
            'flowsn': 25,
            'ordername': 'nhsssyl',
            'beginNo': 1,
            'scdm': '',
            'cpdm': '',
            'jyrq': '',
            'jylsbh': '',
        }

        resp = requests.post(url, data = data, headers = self.HEADERS)
        if resp.status_code != 200:
            logger.error('[Fetch]fetch resp error:%s', resp.status_code)
            return

        return resp.content

    def parse_product_id(self, item):
        '''
        javascript:buy('91117025','0001','20170321','2017032105021675','105','0');
        '''
        RE = '''javascript:buy\('\d+','\d+','\d+','(?P<pid>\d+)','\d+','\d+'\);'''
        info = re.search(RE, item).groupdict()
        return info.get('pid', None)

    def parse(self, resp):
        soup = BeautifulSoup(resp, 'html.parser')
        products = []

        boxes = soup.find_all('div', {'class': 'product-box'})
        if not boxes or len(boxes) != 1:
            return products

        box = boxes[0]
        product_infos = box.find_all('div', {'class': 'product-item'})
        for item in product_infos:
            product = Product()

            product.id = self.parse_product_id(item.a['href'])
            product.title = item.h2.text.strip('\n\r ')
            describes = item.find('div', {'class': 'product-describe'}).find_all('div')
            for describe in describes:
                key = describe.p.text
                value = describe.span.text
                if key == u'转让价格':
                    product.price = value
                elif key == u'自动到期' or key == u'智能续期':
                    product.set_yield_rate(value)

            infos = item.find('div', {'class': 'product-info'}).find_all('em')
            for index, info in enumerate(infos):
                # 截止日期
                if index == 0:
                    product.close_time = info.text
                # 到期日期
                elif index == 1:
                    product.expire_time = info.text

            products.append(product)
            if isinstance(product.yield_rate, float) and product.yield_rate >= 7.0:
                info = ''
                for key, val in iter(product):
                    info += '%s: %s\n' % (key, val)
                print info

        return products


class BankMonitor(object):

    def __init__(self, cookie):
        self.fetcher = BankFetcher(cookie)

    def get_products(self):
        resp = self.fetcher.fetch()
        if resp:
            products = self.fetcher.parse(resp)
            return dict([(item.id, item) for item in products])
        return {}

    def monitor(self):
        while True:
            resp = self.fetcher.fetch()
            if resp:
                products = self.fetcher.parse(resp)
                self.save_product(products)
            time.sleep(5)

    def save_product(self, products):
        info = ''
        for product in products:
            for key, val in product:
                info += '\t%s: %s\n' % (key, val)
            info += '\n'
        logger.info(info)


class BankChangeMonitor(BankMonitor):
    '''
    变动检测
    '''

    def __init__(self, cookie = None):
        super(BankChangeMonitor, self).__init__(cookie)
        self.changes = {}

    def monitor_change(self):
        while True:
            cur = self.get_products()
            self.products_change(cur)

            self.dump_changes()
            time.sleep(5)

    def products_change(self, cur):
        now = str(datetime.datetime.now())

        # 下榜时间
        for pid, change in self.changes.iteritems():
            cur_info = cur.get(pid)
            if not cur_info:
                change.down_time = now

        # 上榜时间
        for pid, product in cur.iteritems():
            change = self.changes.get(pid)
            if change:
                continue

            change = ProductChange()
            change.product_id = pid
            change.product = product
            change.up_time = now
            self.changes[pid] = change

    def dump_changes(self):
        changes = [dict(item) for item in self.changes.values()]
        change_logger.info(json.dumps(changes, indent = 4, ensure_ascii = False))

        '''
        changes = []
        for pid, change in self.changes.iteritems():
            if not changes.up_time or not changes.down_time:
                pass
        '''

if __name__ == '__main__':
    @click.group()
    def cli():
        pass

    @cli.command(name = 'monitor')
    @click.argument('cookie')
    def xy_monitor(cookie):
        '''
        监控
        '''
        monitor = BankMonitor(cookie)
        monitor.monitor()

    @cli.command(name = 'monitor_change')
    @click.argument('cookie', default = '')
    def xy_change_monitor(cookie):
        '''
        变动监控
        '''
        monitor = BankChangeMonitor(cookie)
        monitor.monitor_change()

    @cli.command(name = 'parse')
    @click.argument('filename')
    def cli_parse(filename):
        '''
        解析产品
        '''
        with open(filename, 'rb') as input_file:
            resp = input_file.read()

        fetcher = BankFetcher(None)
        products = fetcher.parse(resp)
        for product in products:
            print str(product)

    cli()
