# -*- coding:utf-8 -*-
# coding=utf-8
__author__ = 'lancger'

from datetime import datetime, timedelta
from flask_wtf import Form
from wtforms import StringField, ValidationError, HiddenField, PasswordField, validators, SelectField, SelectMultipleField
from ..utils.ldap_handle import openldap_conn_open
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users


class SearchServerForm(Form):
    s_content = StringField('搜索内容')
    s_select = SelectField('搜索类型', choices=[('inner_ip', '内网IP'), ('server_name', '服务器名称')])



class ServerAddFromCMDB(Form):
    server_name = SelectMultipleField('server_name', coerce=str)



class AddServerForm(Form):
    server_name = StringField('server_name', [validators.InputRequired(message='服务器名称不能为空')])
    inner_ip = StringField('inner_ip', [validators.InputRequired(message='内网IP不能为空')])
    env = SelectField('category', coerce=int)
    location = SelectField('location', coerce=int)
    type = SelectField('type', coerce=int)
    internet_ip = StringField('internet_ip')
    cpu = StringField('cpu')
    ram = StringField('ram')
    hdd = StringField('hdd')
    status = SelectField('status', coerce=int, default=1)
    desc = StringField('desc')
    business_id = SelectField('business_id', coerce=int)
