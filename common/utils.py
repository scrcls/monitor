#! -*- coding:utf-8 -*-

def to_int(val):
    if not val:
        return 0
    if isinstance(val, str) or isinstance(val, unicode):
        val = val.replace(',', '')
    try:
        return int(val)
    except ValueError as ex:
        return None

def to_float(val):
    if not val:
        return 0
    if isinstance(val, str) or isinstance(val, unicode):
        val = val.replace(',', '')
    try:
        return float(val)
    except ValueError as ex:
        return None

def to_str(val):
    if not val:
        return ''
    if isinstance(val, unicode):
        return val.encode('utf-8')
    return val
