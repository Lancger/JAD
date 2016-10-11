# coding: utf-8
__author__ = 'lancger'

import hashlib

def str_md5(content):
    """将字符串生成md5码"""
    return hashlib.new("md5", content).hexdigest()