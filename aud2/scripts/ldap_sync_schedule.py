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

from app import create_app
from app.views.directory import openldap_sync
app = create_app()
with app.app_context():
    openldap_sync()
