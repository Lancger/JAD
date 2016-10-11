# coding: utf-8
__author__ = 'lancger'

from ._base import db


class Users(db.Model):
    """
    用户表，从ldap同步
    """
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)  #id，递增
    account = db.Column(db.String(20))  #帐号
    uid = db.Column(db.Integer)   #用户id
    username = db.Column(db.String(40))  #真实姓名
    mobile = db.Column(db.String(20))  #手机号码
    email = db.Column(db.String(30))  #邮箱地址
    dn = db.Column(db.String(80))   #对应ldap里面的dn
    depart = db.Column(db.String(80))   #部门

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)
