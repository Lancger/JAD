# coding: utf-8
__author__ = 'lancger'

from datetime import datetime
from ._base import db


class Apps(db.Model):
    """
    应用表，配置应用属性
    """
    __tablename__ = 'apps'
    id = db.Column(db.Integer, primary_key = True)  #应用id，递增
    app_name = db.Column(db.String(40), nullable=False)  #应用名，如aicai_webclient
    status = db.Column(db.SmallInteger)  #状态：0 关闭，1 启用，默认为1
    app_path = db.Column(db.String(100), nullable=False)  #程序部署路径
    tomcat_path = db.Column(db.String(100), nullable=False)  #tomcat部署路径
    port = db.Column(db.Integer, nullable=False)  #服务端口
    shutdown_port = db.Column(db.Integer, nullable=False)  #tomcat shutdown端口
    site = db.Column(db.Integer)  #所属站点，如0 本站，1 新浪站
    rsync_path_name = db.Column(db.Integer, nullable=False)  #rsync服务器配置的路径名称
    # rsync_path_name = db.Column(db.String(40), nullable=False)  #rsync服务器配置的路径名称
    svn_url = db.Column(db.String(100))  #SVN地址
    mvn_command = db.Column(db.String(100))  #MVN打包命令
    java_opts = db.Column(db.String(400))  #tomcat运行JVM配置，保留字段，可为空
    desc = db.Column(db.String(400))  #应用描述
    node = db.relationship('App_nodes', backref = 'apps', lazy = 'dynamic')  #应用部署节点
    business_id = db.Column(db.Integer, nullable=False)   #业务id，关联buisness表id字段
    # business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)   #业务id，关联buisness表id字段

    #插入/更新记录
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    #删除记录
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self


class App_nodes(db.Model):
    """
    应用节点表，配置应用部署在哪些节点上
    """
    __tablename__ = 'app_nodes'
    id = db.Column(db.Integer, primary_key = True)  #id，递增
    app_id = db.Column(db.Integer, db.ForeignKey('apps.id'), nullable=False)  #应用id，关联apps表id字段
    # app_id = db.Column(db.Integer,  nullable=False)  # 应用id，关联apps表id字段
    app_name = db.Column(db.String(40), nullable=False)  #应用名，如aicai_webclient
    # node_id = db.Column(db.Integer, db.ForeignKey('app_servers.id'), nullable=False)  #服务器id
    node_id = db.Column(db.Integer, nullable=False)  # 服务器id
    node_ip = db.Column(db.String(40), nullable=False)  #节点IP
    business_id = db.Column(db.Integer, nullable=False)   #业务id，关联buisness表id字段
    # business_id = db.Column(db.Integer, db.ForeignKey('business.id'), nullable=False)   #业务id，关联buisness表id字段

    #插入/更新记录
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    #删除记录
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self
