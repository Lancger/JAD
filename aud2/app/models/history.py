# coding: utf-8
__author__ = 'lancger'

from datetime import datetime
from ._base import db

# class User_ac_log(db.Model):
class User_ac_log(db.Model):
    """
    用户操作日志表
    """
    __tablename__ = 'User_ac_log'
    id = db.Column(db.Integer, primary_key=True)  # id，递增
    uid = db.Column(db.String(20))  # UID
    account = db.Column(db.String(20))  # 帐号
    ip = db.Column(db.String(40))  # 操作IP
    create_time = db.Column(db.DateTime, nullable=False)  # 创建时间
    action = db.Column(db.String(40))  # 动作/行为
    result = db.Column(db.String(100))  # 结果

    # 插入/更新记录
    def save(self):
        self.create_time = datetime.now()
        db.session.add(self)
        db.session.commit()
        return self

class Message_log(db.Model):
    """
    消息发送日志表
    """
    __tablename__ = 'message_log'
    id = db.Column(db.Integer, primary_key = True)  #id，递增
    receiver = db.Column(db.String(20))  #帐号
    create_time = db.Column(db.DateTime)  #创建时间
    status = db.Column(db.Integer)  #状态,0为未读/未发送，1为已读/已发送
    type = db.Column(db.Integer)  #消息类型，0站内信，1邮件，2短信，3微信
    ext_info = db.Column(db.String(60))  #更多补充信息
    mes_content = db.Column(db.String(600))  #消息内容


    # 插入/更新记录
    def save(self):
        self.create_time = datetime.now()
        db.session.add(self)
        db.session.commit()
        return self


