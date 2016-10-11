# coding: utf-8
__author__ = 'lancger'

from datetime import datetime
from ._base import db


class Business(db.Model):
    """
    业务信息表
    """
    __tablename__ = 'business'
    id = db.Column(db.Integer, primary_key=True)  #主键id  0:彩票业务  1:金融业务   3:滴滴打票业务   4:新增业务
    business_name = db.Column(db.String(40), nullable=False)  #业务名称，彩票业务
    desc = db.Column(db.String(600))  #简单的业务介绍，机房位置等
    beta_ip = db.Column(db.String(40), nullable=False)  #Beta服务器节点
    redis_ip = db.Column(db.String(40), nullable=False) #Redis服务器节点
    redis_port = db.Column(db.Integer)   #Redis服务器节点
    redis_db = db.Column(db.Integer)   #Redis服务器节点

    # 插入/更新记录
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self


class User_business(db.Model):
    """
    用户-业务对应表
    """
    __tablename__ = 'user_business'
    id = db.Column(db.Integer, primary_key=True)  #主键id,递增
    user_id = db.Column(db.Integer)  # 用户id,关联users表id字段
    username = db.Column(db.String(40))  #真实姓名
    business_id = db.Column(db.Integer)  #业务id,关联business表id字段
    business_name = db.Column(db.String(40))  # 业务名称，彩票业务
    create_time = db.Column(db.DateTime)  # 创建时间
    flush_time = db.Column(db.DateTime)  # 更新时间

    # 插入/更新记录
    def save(self):
        self.create_time = datetime.now()
        self.flush_time = datetime.now()
        db.session.add(self)
        db.session.commit()
        return self

    #删除记录
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self


class App_sites(db.Model):
    """
    站点配置表
    """
    __tablename__ = 'app_sites'
    id = db.Column(db.Integer, primary_key=True) #主键id,站点ID，1XXX 前端，2xxx 后端，3xxx 后台
    site_name = db.Column(db.String(40), nullable=False)  #站点名称，爱彩前端，滴滴后端
    status = db.Column(db.Integer, nullable=False)  #状态：0 下线，1 正常；默认为1
    business_id = db.Column(db.Integer)  #业务id,关联business表id字段
    business_name = db.Column(db.String(40))  # 业务名称，彩票业务
    create_time = db.Column(db.DateTime)  # 创建时间
    flush_time = db.Column(db.DateTime)  # 更新时间
    # business_id = db.Column(db.Integer)  #业务id,关联business表id字段
    # create_time = db.Column(db.DateTime, nullable=False)  # 创建时间
    # flush_time = db.Column(db.DateTime, nullable=False)  # 更新时间

    # 插入/更新记录
    def save(self):
        self.create_time = datetime.now()
        self.flush_time = datetime.now()
        db.session.add(self)
        db.session.commit()
        return self

    #删除记录
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    #获取类别名
    def get_site_name(self):
        return site_name


class Site_roles(db.Model):
    """
    项目站点-权限对应表
    """
    __tablename__ = 'site_roles'
    id = db.Column(db.Integer, primary_key=True)  #主键id,递增
    # user_id = db.Column(db.Integer)  # 用户id,关联users表id字段
    # username = db.Column(db.String(40))  #真实姓名
    # business_id = db.Column(db.Integer)  #业务id,关联business表id字段
    # name = db.Column(db.String(40), nullable=False)  # 业务名称，彩票业务
    user_id = db.Column(db.Integer)  # 用户id,关联users表id字段
    username = db.Column(db.String(40))  #真实姓名
    site_id = db.Column(db.Integer)  # 站点id,关联app_sites表id字段
    site_name = db.Column(db.String(40), nullable=False)  # 站点名称，爱彩前端，滴滴后端
    business_id = db.Column(db.Integer)  #业务id,关联business表id字段
    business_name = db.Column(db.String(40), nullable=False)  # 业务名称，彩票业务
    # business_name = db.Column(db.String(40), nullable=False)  # 业务名称，彩票业务
    create_time = db.Column(db.DateTime, nullable=False)  # 创建时间
    flush_time = db.Column(db.DateTime, nullable=False)  # 更新时间

    # 插入/更新记录
    def save(self):
        self.create_time = datetime.now()
        self.flush_time = datetime.now()
        db.session.add(self)
        db.session.commit()
        return self

    #删除记录
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self