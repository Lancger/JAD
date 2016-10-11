# -*- coding:utf-8 -*-
# coding=utf-8
__author__ = 'lancger'

from datetime import datetime, timedelta
from flask_wtf import Form
from wtforms import StringField, ValidationError, HiddenField, PasswordField, validators, SelectField, SelectMultipleField, TextAreaField
from ..utils.ldap_handle import openldap_conn_open
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users


class AddDeployForm(Form):
    app_name = SelectField('app_name', [validators.InputRequired(message='应用名称不能为空')], coerce=str)
    type = SelectField('type', coerce=int, default=1)
    plan = SelectField('plan', coerce=int, default=0)
    env = SelectField('env', coerce=int, default=3)
    message_type = SelectField('message_type', coerce=int, default=1)
    restart_tomcat = SelectField('restart_tomcat', coerce=int, choices=[(0, '不重启'), (1, '重启')], default=0)
    auditor = SelectField('auditor')
    message_cc = SelectMultipleField('message_cc', coerce=str)
    before_command = TextAreaField('before_command')
    after_command = TextAreaField('after_command')
    desc = TextAreaField('desc')
    content = TextAreaField('content')
    subject = StringField('subject')
    business_id = SelectField('business_id', coerce=int)
    # business_id = SelectField('business', coerce=int)

    #需要校验，该应用是否有配置节点，如果没有则需要返回异常
    #未生效
    def validate_app_name(form, field):
        if not App_nodes.query.filter_by(app_id=field.data.split(',')[0]).first():
            raise ValidationError('该应用还未部署节点！')

class EditDeployForm(Form):
    batch_no = StringField('batch_no')
    app_name = StringField('app_name')
    type = SelectField('type', coerce=int, default=1)
    plan = SelectField('plan', coerce=int, default=0)
    env = SelectField('env', coerce=int, default=3)
    message_type = SelectField('message_type', coerce=int, default=1)
    restart_tomcat = SelectField('restart_tomcat', coerce=int, choices=[(0, '不重启'), (1, '重启')], default=0)
    auditor = SelectField('auditor')
    message_cc = SelectMultipleField('message_cc', coerce=str)
    before_command = TextAreaField('before_command')
    after_command = TextAreaField('after_command')
    desc = TextAreaField('desc')
    content = TextAreaField('content')
    subject = StringField('subject')
    business_id = SelectField('business_id', coerce=int)


class AddRestartForm(Form):
    # app_name = SelectField('app_name', [validators.InputRequired(message='应用名称不能为空')], coerce=str)
    subject = StringField('subject')
    app_name = SelectField('app_name')
    auditor = SelectField('auditor')