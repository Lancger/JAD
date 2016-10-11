# coding: utf-8
__author__ = 'lancger'

import string
import random
import requests
from flask import current_app


def gen_sms_vcode():
    """
    生成N(SMS_CODE_LENGTH)位随机验证码
    """
    config = current_app.config

    _vlength = config.get('SMS_CODE_LENGTH')
    return ''.join([random.choice(string.digits) for i in range(_vlength)])


def send_sms(mobile, content):
    """
    调用公司短信网关发送短信
    """
    config = current_app.config
    req_send_sms_url = config.get('SMS_URL')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'}
    payload = {}
    payload["telNumber"] = mobile
    payload["source"] = "s0006"
    payload["content"] = content

    r = requests.get(req_send_sms_url, params=payload, headers=headers)

    if r.status_code == 200:
        return True
    else:
        return False


def shadow_phone(phone):
    _len = 5  # 遮挡中间6位,前3,后2
    p = phone[:3] + '*' * _len + phone[9:]
    return p

