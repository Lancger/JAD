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
from flask import render_template, current_app
from app import create_app
from app.mails import send_simple_mail
from app.models import LDAP_User, Sys_Users_Role, Mail_send_history

app = create_app()

# 获取当天日期
today_date = datetime.now()
today = today_date.strftime("%Y-%m-%d")

with app.app_context():
    user_list = LDAP_User.query.with_entities(LDAP_User.cn,
                                              Sys_Users_Role.pwd_change_time,
                                              Sys_Users_Role.status,
                                              Sys_Users_Role.pwd_never_outdate).filter(
        Sys_Users_Role.uid == LDAP_User.uidnumber,
        Sys_Users_Role.pwd_change_time < (
        datetime.now() - timedelta(days=current_app.config.get('PASSWD_EXPIRE_ALERT_DAYS'))),
        Sys_Users_Role.pwd_never_outdate == 0,
	    #LDAP_User.depart.like('%系统运维部%'),
        #LDAP_User.cn == 'xuki.xu',  # 生产环境注释
        Sys_Users_Role.status == 0, ).all()

    # 发送邮件
    for user in user_list:

        passwd_expire_date = user.pwd_change_time + timedelta(days=90)

        # 渲染邮件模板
        html = render_template('email/passwd_outdate.html',
                               account=user.cn,
                               expire_date=passwd_expire_date.strftime("%Y/%m/%d"),
                               today=today)

        #app.logger.info('用户: %s ,密码即将(20天内)过期提醒邮件已发送。' % user.cn)
        if send_simple_mail(subject='新浪爱彩内部帐号密码过期提醒【重要】', to_who=user.cn, html_body=html):

            app.logger.info('用户: %s ,密码即将(20天内)过期提醒邮件已发送。' % user.cn)

            # 保存邮件发送记录
            msh_record = Mail_send_history(to_who=user.cn,
                                           content='email/passwd_outdate.html')
            msh_record.save()

        time.sleep(5)
