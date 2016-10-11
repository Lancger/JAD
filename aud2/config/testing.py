# coding: utf-8
__author__ = 'lancger'

from .default import Config


class TestingConfig(Config):
    # App config
    TESTING = True
    DEBUG = True
    SQLALCHEMY_RECORD_QUERIES = True

    #数据库连接配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@localhost/aud?charset=utf8'

    #LDAP服务器配置
    OPENLDAP_SERVER_URI = 'ldap://192.168.90.141:389'
    OPENLDAP_BASE_DN = 'dc=aicai,dc=com'
    OPENLDAP_LOGIN_USER = 'cn=Manager,dc=aicai,dc=com'
    OPENLDAP_LOGIN_PASSWD = 'UthaidoaF5Iemius'
