# coding: utf-8
__author__ = 'lancger'

from .default import Config


class ProductionConfig(Config):
    # App config
    DEBUG = False

    WTF_CSRF_CHECK_DEFAULT = False
    #数据库连接配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:zwc123@192.168.66.93/aud?charset=utf8'
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:zwc123@localhost/aud2?charset=utf8'

    #LDAP服务器配置
    LDAP_SERVER_URI = 'ldap://192.168.90.159:389'
    LDAP_BASE_DN = 'dc=aicai,dc=com'
    LDAP_LOGIN_USER = 'cn=aicaiadmin,ou=authusers,dc=aicai,dc=com'
    LDAP_LOGIN_PASSWD = 'Yae0zohV2mieJooCho'
