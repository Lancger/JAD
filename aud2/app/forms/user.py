# -*- coding:utf-8 -*-
# coding=utf-8
__author__ = 'lancger'

from flask_wtf import Form
from wtforms import StringField, ValidationError, TextAreaField, SelectMultipleField, SelectField, HiddenField, \
    PasswordField, validators
from ..utils.ldap_handle import openldap_conn_open


class UserSearchForm(Form):
    """
    用户列表搜索
    """
    s_content = StringField('搜索用户')
    s_select = SelectField('搜索方式', choices=[('cn', '用户名'), ('sn', '真实姓名'), ('depart', '部门')])


class addUserForm(Form):
    """
    增加用户
    """
    account = StringField('account', [validators.InputRequired(message='请输入帐号名称')])
    name = StringField('name', [validators.InputRequired(message='请输入真实姓名')])
    mobile = StringField('mobile',
                         [validators.InputRequired(message='手机号码不能为空'),
                          validators.Regexp(r'^1[3|4|5|7|8|9][0-9]\d{8}$', message='手机号码格式错误，例：13512345678')],
                         default='13800138000')
    depart = SelectField('depart', coerce=str)
    perm_group = SelectMultipleField('perm_group', coerce=int)

    #根据帐号检验用户是否存在，如果存在则返回错误消息
    def validate_account(form, field):
        #实例化utils.ldapHandle，连接好ldap，并准备好接受查询
        ldap_conn = openldap_conn_open()

        if ldap_conn.ldap_get_a_user(search_cn=field.data):
            raise ValidationError('帐号已存在！')
