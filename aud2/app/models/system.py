# coding: utf-8
__author__ = 'lancger'

from ._base import db


class System(db.Model):
    """
    系统配置表
    """
    __tablename__ = 'system'
    id = db.Column(db.Integer, primary_key = True)  #主键id，递增
    config_name = db.Column(db.String(60))   #配置项
    config_value = db.Column(db.String(60))   #配置值
    description = db.Column(db.String(100))   #配置项说明
