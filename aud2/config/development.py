# coding: utf-8
__author__ = 'lancger'

from .default import Config


class DevelopmentConfig(Config):
    # App config
    DEBUG = True
    SQLALCHEMY_RECORD_QUERIES = True

    # #LDAP服务器配置
    # LDAP_SERVER_URI = 'ldap://192.168.90.141:389'
    # LDAP_BASE_DN = 'dc=aicai,dc=com'
    # LDAP_LOGIN_USER = 'cn=Manager,dc=aicai,dc=com'
    # LDAP_LOGIN_PASSWD = 'UthaidoaF5Iemius'

    #LDAP服务器配置
    LDAP_SERVER_URI = 'ldap://192.168.90.159:389'
    LDAP_BASE_DN = 'dc=aicai,dc=com'
    LDAP_LOGIN_USER = 'cn=aicaiadmin,ou=authusers,dc=aicai,dc=com'
    LDAP_LOGIN_PASSWD = 'Yae0zohV2mieJooCho'

    #AD服务器配置
    AD_SERVER_URI = 'ldaps://192.168.91.189:636'
    AD_BASE_DN = 'dc=aicai,dc=cn'
    AD_LOGIN_USER = 'CN=Administrator,CN=Users,DC=aicai,DC=cn'
    AD_LOGIN_PASSWD = 'zwc123!@#'

