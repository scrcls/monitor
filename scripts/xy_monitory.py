#! -*- coding:utf-8 -*-
import importme

from common.logger import setup_logger

from bs4 import BeautifulSoup
import logging
import json
import requests
import time

logger = setup_logger('monitory', 'monitor.log', logging.DEBUG)

class Product(object):
    def __init__(self):
        self.title = ''
        self.price = None
        self.yield_rate = None
        self.close_time = None
        self.expire_time = None

    def __iter__(self):
        return iter([
            ('title', self.title),
            ('price', self.price),
            ('yield_rate', self.yield_rate),
            ('close_time', self.close_time),
            ('expire_time', self.expire_time),
        ])


class BankFetcher(object):

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Cookie': 'Hm_lvt_9311ae0af3818e9231e72458be9cdbce=1490088074,1490088398,1490088508,1490088540; Hm_lpvt_9311ae0af3818e9231e72458be9cdbce=1490088552; JSESSIONID=cDpTYRXJTn1GLTtMQ0B8GZ9QQ5hDRYn1GqKfzjyn9h71hKyTZ8g9!216974286',
    }

    def __init__(self):
        pass

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

    def parse(self, resp):
        soup = BeautifulSoup(resp, 'html.parser')
        products = []

        boxes = soup.find_all('div', {'class': 'product-box'})
        if not boxes or len(boxes) != 1:
            print 'boxes'
            return products

        box = boxes[0]
        product_infos = box.find_all('div', {'class': 'product-item'})
        for item in product_infos:
            product = Product()

            product.title = item.h2.text.strip('\n\r ')
            describes = item.find('div', {'class': 'product-describe'}).find_all('div')
            for describe in describes:
                key = describe.p.text
                value = describe.span.text
                if key == u'转让价格':
                    product.price = value
                elif key == u'自动到期' or key == u'智能续期':
                    product.yield_rate = value

            infos = item.find('div', {'class': 'product-info'}).find_all('em')
            for index, info in enumerate(infos):
                if index == 0:
                    product.close_time = info.text
                elif index == 1:
                    product.expire_time = info.text

            products.append(product)
        return products


class BankMonitor(object):

    def __init__(self):
        self.fetcher = BankFetcher()

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

if __name__ == '__main__':
    monitor = BankMonitor()
    monitor.monitor()
