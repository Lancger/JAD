# -*- coding:utf-8 -*-
# coding=utf-8
__author__ = 'lancger'

from datetime import datetime, timedelta
from flask_wtf import Form
from wtforms import StringField, ValidationError, HiddenField, PasswordField, validators, SelectField, SelectMultipleField
from ..utils.ldap_handle import openldap_conn_open
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users

# class SearchAppForm(Form):
#     s_content = StringField('搜索内容')
#     s_select = SelectField('搜索类型', choices=[('app_name', '应用名称'), ('port', '服务端口')])


class SearchAppForm(Form):
    s_content = StringField('搜索内容')

class SearchAppRoleForm(Form):
    s_content = StringField('搜索内容')

class AddAppNodeForm(Form):
    node_ip = SelectField('node_ip', coerce=str)

class AddAppForm(Form):
    app_name = StringField('应用名', [validators.InputRequired(message='应用名称不能为空')])
    status = SelectField('状态', coerce=int, choices=[(0, '禁用'), (1, '启用')], default=1)
    app_path = StringField('程序路径', [validators.InputRequired(message='程序部署路径不能为空')])
    tomcat_path = StringField('Tomcat路径')
    port = StringField('服务端口')
    shutdown_port = StringField('关闭端口')
    svn_url = StringField('svn_url')
    #mvn_command = StringField('mvn_command', [validators.InputRequired(message='MVN打包命令不能为空')])
    #java_opts = TextAreaField('JVM参数')
    #beta_server = SelectField('beta_server', coerce=str)
    #business_id = SelectField('business_id', coerce=str)
    business_id = SelectField('业务类别', coerce=int)
    rsync_path_name = SelectField('rsync_path_name', coerce=str)
    site = SelectField('站点', coerce=int)
    desc = StringField('备注说明')

    #检查同一环境下应用名是否重复添加

class SearchAppForm(Form):
    s_content = StringField('搜索内容')
    s_select = SelectField('搜索类型', choices=[('app_name', '应用名称'), ('port', '服务端口')])


class BatchForm(Form):
    app = SelectMultipleField('app', coerce=int, choices=[])
    # group = SelectMultipleField('group', coerce=int, choices=[])

