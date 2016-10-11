# coding: utf-8
__author__ = 'lancger'

from datetime import datetime
from ._base import db

#新增的一个表
class App_tomcat_restart(db.Model):
    """
    应用重启批次表
    """
    __tablename__ = 'app_tomcat_restart'
    id = db.Column(db.Integer, primary_key=True)  # 主键id，递增
    batch_no = db.Column(db.String(40), nullable=False)  # 重启批次
    app_id = db.Column(db.Integer, nullable=False)  # 应用id，关联apps表id字段
    app_name = db.Column(db.String(40), nullable=False)  # 应用名，如aicai_webclient
    business_id = db.Column(db.Integer)  # 业务id,关联business表id字段
    status = db.Column(db.Integer)  # 状态，0.审批中 1.审批通过  2.审批驳回
    create_time = db.Column(db.DateTime, nullable=False)  # 创建时间
    audit_time = db.Column(db.DateTime)   #审批时间
    finish_time = db.Column(db.DateTime)  #完成时间
    launcher = db.Column(db.String(20))   #发起人
    auditor = db.Column(db.String(20))    #审批人
    operator = db.Column(db.String(20))  # 操作人
    subject = db.Column(db.String(200))  # 重启原因


    # 插入/更新记录
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

class App_tomcat_his(db.Model):
    """
    节点部署Tomcat历史表
    """
    __tablename__ = 'app_tomcat_his'
    id = db.Column(db.Integer, primary_key = True)  #主键id，递增
    batch_id = db.Column(db.Integer)  #更新批次表id
    batch_no = db.Column(db.String(40))  #更新批次
    task_no = db.Column(db.String(60), nullable=False)  #任务号
    app_id = db.Column(db.Integer)  #应用id，关联apps表id字段
    app_name = db.Column(db.String(40), nullable=False)  #应用名，如aicai_webclient
    create_time = db.Column(db.DateTime, nullable=False)  #创建时间
    # node_id = db.Column(db.Integer, db.ForeignKey('app_servers.id'), nullable=False)  #服务器id
    node_id = db.Column(db.Integer, nullable=False)  # 服务器id
    node_ip = db.Column(db.String(40), nullable=False)  #部署节点
    app_path = db.Column(db.String(100), nullable=False)  #程序部署路径
    tomcat_path = db.Column(db.String(100), nullable=False)  #tomcat部署路径
    port = db.Column(db.Integer, nullable=False)  #服务端口
    type = db.Column(db.Integer)  #类型，0 部署，1 移除，2 重启
    status = db.Column(db.Integer)  #状态，0 排队中，1 操作中，2 异常，3成功
    finish_time = db.Column(db.DateTime)   #完成时间
    conclusion = db.Column(db.String(10))   #tomcat重启结果
    detail = db.Column(db.String(1000))   #异常描述

    #插入/更新记录
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self