# -*- coding:utf-8 -*-
# coding=utf-8
__author__ = 'lancger'

import os
import sys
# 将project目录加入sys.path
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

reload(sys)
sys.setdefaultencoding('utf-8')

import datetime
from timeit import default_timer
from flask import Flask, request, g, render_template, current_app, session, redirect
from flask.ext.login import LoginManager, current_user
from flask.ext.bootstrap import Bootstrap
from flask_debugtoolbar import DebugToolbarExtension
from flask_wtf.csrf import CsrfProtect
import logging
from logging.handlers import RotatingFileHandler
from flask_sqlalchemy import get_debug_queries
from config import load_config
from models import db, Users, Users_role, Roles

csrf = CsrfProtect()


def create_app():
    """
    构建应用
    """
    app = Flask(__name__)
    config = load_config()
    app.config.from_object(config)

    bootstrap = Bootstrap(app)

    # CSRF protect
    csrf.init_app(app)
    # app.config.setdefault('WTF_CSRF_CHECK_DEFAULT', False)
    # app.config["WTF_CSRF_CHECK_DEFAULT"] = False

    if app.debug:
        DebugToolbarExtension(app)

    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

    register_db(app)
    register_jinja(app)
    register_error_handle(app)
    register_logger(app)
    register_login(app)
    register_before_handlers(app)
    register_after_handlers(app)
    register_extensions(app)
    register_routes(app)

    return app


def register_db(app):
    """
    数据库
    """
    from .models import db

    db.init_app(app)


def register_jinja(app):
    """
    模板相关
    """
    from . import filters

    app.jinja_env.filters.update({
        'str_md5': filters.str_md5
    })


def register_logger(app):
    """
    日志记录
    """
    """Send error log to admin by smtp"""
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')

    debug_log = os.path.join(app.root_path,
                             app.config['DEBUG_LOG'])

    debug_file_handler = \
        RotatingFileHandler(debug_log,
                            maxBytes=100000,
                            backupCount=10)

    debug_file_handler.setLevel(logging.DEBUG)
    debug_file_handler.setFormatter(formatter)
    app.logger.addHandler(debug_file_handler)

    error_log = os.path.join(app.root_path,
                             app.config['ERROR_LOG'])
    # print "mmm"*20
    # print error_log
    # print "mmm"*20

    error_file_handler = \
        RotatingFileHandler(error_log,
                            maxBytes=100000,
                            backupCount=10)

    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    app.logger.addHandler(error_file_handler)


def register_routes(app):
    """
    访问路径和蓝图
    """
    from .views import site, user, perm, system, self, servers, business, deploy, tomcat, api

    app.register_blueprint(site.bp, url_prefix='')
    app.register_blueprint(user.bp, url_prefix='/user')
    app.register_blueprint(perm.bp, url_prefix='/perm')
    app.register_blueprint(system.bp, url_prefix='/sys')
    app.register_blueprint(self.bp, url_prefix='/self')
    app.register_blueprint(servers.bp, url_prefix='/servers')
    app.register_blueprint(business.bp, url_prefix='/business')
    app.register_blueprint(deploy.bp, url_prefix='/deploy')
    app.register_blueprint(tomcat.bp,url_prefix='/tomcat')
    app.register_blueprint(api.bp, url_prefix='/api')
    # csrf.exempt(site.bp)
    # csrf.exempt(tomcat.bp)
    # csrf.exempt(api)

def register_error_handle(app):
    """
    错误页面
    """

    @app.errorhandler(403)
    def page_403(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_404(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def page_500(error):
        return render_template('errors/500.html'), 500


def register_login(app):
    """
    登录相关
    """
    login_manager = LoginManager()
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    # session超时设置为30分钟
    app.permanent_session_lifetime = datetime.timedelta(minutes=30)

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        session['next_url'] = request.path
        return redirect('login')

    @login_manager.user_loader
    def load_user(userid):
        #return Sys_Users_Role.query.filter(Sys_Users_Role.uid == userid).first()
        return Users_role.query.filter(Users_role.uid == userid).first()


def register_before_handlers(app):
    """
    before_request
    """

    @app.before_request
    def before_request():
        g.user = current_user


        g.config = current_app.config

        # 获取用户IP
        headers_list = request.headers.getlist("X-Forwarded-For")
        g.user_real_ip = headers_list[0] if headers_list else request.remote_addr

        #session超时设置
        session.permanent = True

        #保存初始时间
        g.starttime = default_timer()


def register_after_handlers(app):
    """
    after_request
    """

    @app.after_request
    def record_queries(response):

        # 数据库执行调试输出
        for info in get_debug_queries():
            print info

        # 权限调试信息
        if current_app.debug:
            if current_user is not None and current_user.is_authenticated():
                #print session['account']
                #print session['user_tag']
                #print "current_user.is_hr:%s" % current_user.is_hr()
                #print "current_user.is_ss:%s" % current_user.is_ss()
                print "current_user.is_admin:%s" % current_user.is_admin()

        # page_ex_time = int(round((default_timer() - g.starttime) * 1000, 2))
        page_ex_time = 30

        ##输出页面执行时间
        if (response.response and response.content_type.startswith("text/html") and response.status_code == 200):
            response.response[0] = response.response[0].replace("<|pageruntime|>", str(page_ex_time))
        return response


def register_extensions(app):
    """
    其它扩展功能，如邮箱、短信
    """
    from .mails import mail

    mail.init_app(app)


