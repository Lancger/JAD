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

from datetime import datetime, timedelta
from flask import current_app
from app.views.user import ad_user_lock, ldap_user_lock
from app.models import LDAP_User, Sys_Users_Role, User_action_log
from app import create_app

app = create_app()

with app.app_context():
    passwd_expired_user_list = LDAP_User.query.with_entities(LDAP_User.cn,
                                                             Sys_Users_Role.pwd_change_time,
                                                             Sys_Users_Role.status,
                                                             Sys_Users_Role.pwd_never_outdate).filter(
        Sys_Users_Role.uid == LDAP_User.uidnumber,
        Sys_Users_Role.pwd_change_time < (
        datetime.now() - timedelta(days=current_app.config.get('PASSWD_EFFECT_DAYS'))),
        Sys_Users_Role.pwd_never_outdate == 0,
        LDAP_User.cn == 'yu.wang',  # 生产环境注释
        Sys_Users_Role.status == 0, ).all()

    # 锁定帐号
    for user in passwd_expired_user_list:
        app.logger.info('用户: %s ,密码已过期(90天)，帐号已锁定。' % user.cn)

        if ldap_user_lock(user.cn):

            user_role = Sys_Users_Role.query.filter(Sys_Users_Role.account == user.cn).first_or_404()
            # 修改用户状态为禁用(1)
            user_role.status = 1
            user_role.save()

            # 保存操作记录
            user_ac_record = User_action_log(uid='0',
                                             account='sys_auto',
                                             ip='127.0.0.1',
                                             action='user_disable',
                                             ac_object=user.cn,
                                             result='True')
            # 写入数据库
            user_ac_record.save()

            # 锁定ad帐号
            if ad_user_lock(user.cn):
                # 保存操作记录
                user_ac_record = User_action_log(uid='0',
                                                 account='sys_auto',
                                                 ip='127.0.0.1',
                                                 action='user_ad_disable',
                                                 ac_object=user.cn,
                                                 result='True')
                # 写入数据库
                user_ac_record.save()
            else:
                # 保存操作记录
                user_ac_record = User_action_log(uid='0',
                                                 account='sys_auto',
                                                 ip='127.0.0.1',
                                                 action='user_ad_disable',
                                                 ac_object=user.cn,
                                                 result='False')
                # 写入数据库
                user_ac_record.save()
        else:
            # 保存操作记录
            user_ac_record = User_action_log(uid='0',
                                             account='sys_auto',
                                             ip='127.0.0.1',
                                             action='user_disable',
                                             ac_object=user.cn,
                                             result='False')
            # 写入数据库
            user_ac_record.save()
