#! -*- coding:utf-8 -*-
import importme

import json
import requests
from bs4 import BeautifulSoup

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

class BankFetch(object):

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Host': '3g.cib.com.cn',
        'Origin': 'https://3g.cib.com.cn',
    }

    def __init__(self):
        pass

    def fetch(self, page = 1):
        url = 'https://3g.cib.com.cn/app/20071.html'
        data = {
            'viewflag': 0,
            'flowsn': 25,
            'ordername': 'nhsssyl',
            'beginNo': 1,
        }

        resp = requests.post(url, data = data, headers = self.HEADERS)

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

            product.title = item.h2.text.strip('\n\r ')
            describes = item.find('div', {'class': 'product-describe'}).find_all('div')
            for describe in describes:
                key = describe.p.text
                value = describe.span.text
                if key == u'转让价格':
                    product.price = value
                elif key == u'自动到期':
                    product.yield_rate = value

            infos = item.find('div', {'class': 'product-info'}).find_all('em')
            for index, info in enumerate(infos):
                if index == 0:
                    product.close_time = info.text
                elif index == 1:
                    product.expire_time = info.text
            
            products.append(product)
        return products

if __name__ == '__main__':
    fetcher = BankFetch()
    fetcher.fetch()
    fetcher.parse(resp_html)
    #resp_html = open('/home/vagrant/monitor/xy.html').read()
