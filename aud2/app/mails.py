# -*- coding:utf-8 -*-
#coding=utf-8
__author__ = 'lancger'

import hashlib
from flask import render_template, url_for, current_app
from flask_mail import Message, Mail

mail = Mail()
