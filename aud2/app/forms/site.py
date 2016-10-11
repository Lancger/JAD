# -*- coding:utf-8 -*-
# coding=utf-8
__author__ = 'xujing'

from flask_wtf import Form
from wtforms import StringField, ValidationError, BooleanField, PasswordField, validators,SelectField
from ..utils.ldap_handle import openldap_conn_open
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users


class SearchSiteForm(Form):
    s_content = StringField('搜索内容')


class AddAppForm(Form):
    app_name = StringField('应用名', [validators.InputRequired(message='应用名称不能为空')])
    status = SelectField('状态', coerce=int, choices=[(0, '禁用'), (1, '启用')], default=1)
    app_path = StringField('程序路径', [validators.InputRequired(message='程序部署路径不能为空')])
    tomcat_path = StringField('Tomcat路径')
    port = StringField('服务端口')
    shutdown_port = StringField('关闭端口')
    svn_url = StringField('svn_url')
    #mvn_command = StringField('mvn_command', [validators.InputRequired(message='MVN打包命令不能为空')])
    #java_opts = TextAreaField('JVM参数')
    #beta_server = SelectField('beta_server', coerce=int)
    business_id = SelectField('business_id', coerce=int)
    rsync_path_name = SelectField('rsync_path_name', coerce=str)
    site = SelectField('站点', coerce=int)
    desc = StringField('备注说明')

    #检查同一环境下应用名是否重复添加

class AddSiteForm(Form):
    site_name = StringField('site_name', [validators.InputRequired(message='应用类别名称不能为空')])
    business_id = SelectField('business_id', coerce=int)
    business_name = StringField('business_name', [validators.InputRequired(message='业务大类名称不能为空')])
    site_type = SelectField('type', coerce=int)

class AddSiteRoleForm(Form):
    user_id = SelectField('user_id', coerce=int)
    site_id = SelectField('id', coerce=int)


class SearchSiteoleForm(Form):
    s_content = StringField('搜索内容')


class LoginForm(Form):
    """
    登录表单
    """
    account = StringField('account', [validators.InputRequired(message='请输入爱彩帐号名,如:san.zhang'),
                                      validators.length(min=4, max=30, message='用户名至少4位')])
    password = PasswordField('password', [validators.InputRequired(message='请输入密码'),
                                          validators.length(min=6, max=20, message='密码至少6位')])
    remember_me = BooleanField('remember_me', default=False)

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    # 验证帐号是否存在
    def validate_account(self, field):
        try:
            LDAP_User.query.filter_by(cn=field.data).first_or_404()
        except:
            raise ValidationError('用户名或密码错误！')

    # 验证密码是否正确
    def validate_password(self, field):
        # 实例化utils.ldapHandle，连接好ldap，并准备好接受查询
        ldap_conn = openldap_conn_open()

        try:
            if not ldap_conn.ldap_user_auth(uid=self.account.data, passwd=field.data):
                raise ValidationError('用户名或密码错误！')
        except:
            raise ValidationError('用户名或密码错误！')


