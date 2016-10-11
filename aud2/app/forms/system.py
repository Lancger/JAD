# -*- coding:utf-8 -*-
#coding=utf-8
__author__ = 'xujing'

from flask_wtf import Form
from wtforms import SelectField

class ChangeRoleform(Form):
    role = SelectField('role', coerce=int)
