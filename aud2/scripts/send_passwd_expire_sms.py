#! /home/www/.virtualenvs/devenv/bin/python
# -*- coding: utf-8 -*-
# #coding=utf-8
import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))
reload(sys)
sys.setdefaultencoding('utf-8')

if 'AUTODEPLOY_APP_MODE' not in os.environ:
    os.environ['AUTODEPLOY_APP_MODE'] = 'PRODUCTION'

import time
from datetime import datetime, timedelta
from flask import current_app
from app import create_app
from app.mails import send_simple_mail
from app.models import LDAP_User, Sys_Users_Role, SMS_send_history
from app.utils.sms import send_sms

app = create_app()

# 获取当天日期
today_date = datetime.now()
today = today_date.strftime("%Y-%m-%d")

with app.app_context():
    user_list = LDAP_User.query.with_entities(LDAP_User.cn,
                                              LDAP_User.mobile,
                                              Sys_Users_Role.pwd_change_time,
                                              Sys_Users_Role.status,
                                              Sys_Users_Role.pwd_never_outdate).filter(
        Sys_Users_Role.uid == LDAP_User.uidnumber,
        # Sys_Users_Role.pwd_change_time < (
        #    datetime.now() - timedelta(days=3)),
        Sys_Users_Role.pwd_never_outdate == 0,
        # LDAP_User.depart.like('%系统运维部%'),
        LDAP_User.cn == 'xuki.xu',  # 生产环境注释
        Sys_Users_Role.status == 0, ).all()

    config = current_app.config

    # 发送短信
    for user in user_list:

        passwd_expire_date = user.pwd_change_time + timedelta(days=90)

        # 短信内容
        sms_content = config.get('SMS_PASSWD_EXPIRE_MES') % (user.cn, passwd_expire_date.strftime("%Y/%m/%d"), today)

        if send_sms(user.mobile, sms_content):
            app.logger.info('用户: %s ,密码即将(3天内)过期提醒短信已发送。' % user.cn)

            # 保存邮件发送记录
            msh_record = SMS_send_history(to_who=user.cn,
                                          mobile=user.mobile,
                                          content='密码即将(3天内)过期提醒短信')
            msh_record.save()

        time.sleep(5)
