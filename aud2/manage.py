#!/home/dev/demo/bin/python
# -*- coding: utf-8 -*-
#coding=utf-8
__author__ = 'lancger'

from flask.ext.script import Manager, prompt_bool
from flask.ext.migrate import Migrate, MigrateCommand
from app import create_app
from app.models import db

app = create_app()
manager = Manager(app)
db.init_app(app)

# 添加migrate命令
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def run():
    """启动app"""
    app.run(debug=True)

@manager.command
def createall():
    """ 创建数据库表 """
    db.create_all()

@manager.command
def dropall():
    """ 删除所有数据库表 """

    if prompt_bool("Are you sure ? You will lose all your data !"):
        db.drop_all()

if __name__ == '__main__':
    manager.run()

