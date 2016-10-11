# -*- coding:utf-8 -*-
#coding=utf-8
__author__ = 'xujing'

from flask_wtf import Form
from wtforms import StringField, SelectMultipleField, validators, SelectField


class AddUserToPermConfig(Form):
    """
    增加用户到权限组
    """
    user = SelectMultipleField('user', coerce=str)


class ChangeRoleform(Form):
    role = SelectField('role', coerce=int)


class AddPermGroup(Form):
    """
    增加新的用户权限组
    """
    new_perm_group = StringField('new_perm_group', [validators.InputRequired(message='名称不能为空！')])