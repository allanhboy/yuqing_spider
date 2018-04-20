# -*- coding: utf-8 -*-
import chardet
import sys
sys.setrecursionlimit(1000000)
def get_encoding(s):
    '''
    获取文字编码
    '''
    try:
        chardit1 = chardet.detect(s)
        if chardit1['encoding'] == "utf-8" or chardit1['encoding'] == "UTF-8":
            return "UTF-8"
        else:
            return "GBK"
    except:
        return "UTF-8"