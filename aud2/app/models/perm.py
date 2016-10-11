# coding: utf-8
__author__ = 'lancger'


from ._base import db


class Roles(db.Model):
    """
    角色表
    """
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key = True)  #id，递增
    role = db.Column(db.String(40), nullable=False)  #角色
    desc = db.Column(db.String(100), nullable=False)  #角色描述

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

class Users_role(db.Model):
    """
    用户角色关联表
    """
    __tablename__ = 'users_role'
    id = db.Column(db.Integer, primary_key = True)  #id，递增
    uid = db.Column(db.String(20))  #UID
    account = db.Column(db.String(20))  #帐号
    username = db.Column(db.String(40))  #真实姓名
    role_id = db.Column(db.Integer)   #角色id
    last_login_time = db.Column(db.DateTime)   #最后登录时间
    last_login_ip = db.Column(db.String(40))  #最后登录IP

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
        return unicode(self.uid)

    def is_developer(self):
        if self.role_id == 2 or self.account == 'xuki.xu' or self.account == 'manbo.xu':
            return True
        else:
            return False

    def is_auditor(self):
        if self.role_id == 3 or self.account == 'xuki.xu' or self.account == 'manbo.xu':
            return True
        else:
            return False

    def is_sa(self):
        if self.role_id == 4 or self.account == 'xuki.xu' or self.account == 'manbo.xu':
            return True
        else:
            return False

    def is_admin(self):
        if self.role_id == 5 or self.account == 'xuki.xu' or self.account == 'manbo.xu':
            return True
        else:
            return False
