# -*- coding:utf-8 -*-
# coding=utf-8
__author__ = 'lancger'

from flask_wtf import Form
from wtforms import StringField, ValidationError, TextAreaField, SelectMultipleField, SelectField, HiddenField, \
    PasswordField, validators, IntegerField
from ..utils.ldap_handle import openldap_conn_open


class SearchBusinessForm(Form):
    s_content = StringField('搜索内容')


class AddBusinessForm(Form):
    business_name = StringField('业务名', [validators.InputRequired(message='应用名称不能为空')])
    desc = StringField('备注说明')
    beta_ip = StringField('Beta', [validators.InputRequired(message='beta不能为空')])
    redis_ip = StringField('redis', [validators.InputRequired(message='redis不能为空')])
    redis_port = IntegerField('redis_port',  [validators.InputRequired(message='redis_port不能为空')])
    redis_db = IntegerField('redis_db',  [validators.InputRequired(message='redis_db不能为空')])


class AddBusinessRoleForm(Form):
    user_id = SelectField('user_id', coerce=int)
    business_id = SelectField('business_id', coerce=int)