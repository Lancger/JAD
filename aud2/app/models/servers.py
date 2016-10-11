# coding: utf-8
__author__ = 'lancger'

from datetime import datetime
from ._base import db


class App_servers(db.Model):
    """
    应用服务器表，配置应用属性
    """
    __tablename__ = 'app_servers'
    id = db.Column(db.Integer, primary_key = True)  #应用id，递增
    server_name = db.Column(db.String(40), nullable=False)  #服务器名称
    inner_ip = db.Column(db.String(40))  #内网IP
    env = db.Column(db.Integer, nullable=False)  #类别：0 测试环境，1 beta环境，2 生产环境
    location = db.Column(db.Integer, nullable=False)  #服务器位置，0 公司机房，1 广州七星岗电信，2 广州沙溪电信，3 北京北显联通，4 深圳龙岗电信，5 阿里云杭州
    type = db.Column(db.Integer, nullable=False)  #服务器类型，0 物理机，1，KVM虚拟机，2 LXC容器
    internet_ip = db.Column(db.String(40))  #外网IP
    cpu = db.Column(db.Integer, nullable=False)  #CPU配置，单位为核数，如2 代表2 core
    ram = db.Column(db.Integer, nullable=False)  #内存配置，单位为G
    hdd = db.Column(db.Integer, nullable=False)  #硬盘配置，单位为G
    status = db.Column(db.Integer, nullable=False)  #状态：0 下线，1 正常；默认为1
    desc = db.Column(db.String(40))   #备注说明
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