# coding: utf-8
__author__ = 'lancger'

from flask import render_template, request, redirect, url_for, Blueprint, flash, g, \
    session, current_app, jsonify, json
from .. import models
from ..utils.message import Mess
from app import csrf
from flask.ext.login import login_user, logout_user, login_required
from datetime import datetime, date, timedelta
from ..forms import LoginForm, SearchSiteForm, SearchServerForm, SearchAppForm, AddSiteForm, AddSiteRoleForm, SearchSiteoleForm, SearchAppRoleForm
from ..models import  User_ac_log, Users_role,  Apps, App_servers, App_nodes, System, Users, Site_roles, App_sites
from sqlalchemy import desc, func
from ..utils.ldap_handle import openldap_conn_open
from ..utils.ldap_sync_user import ldapConnOpen, ldapHandle
from ..permissions import UserPermission, DeveloperPermission, AuditorPermission, SAPermission, AdminPermission

bp = Blueprint('site', __name__)


@bp.route('/')
@bp.route('/index')
@login_required
#@SSPermission()
def index():
    """
    首页
    """
    count_dic = {}

    #项目数量
    apps_count = models.Apps.query.count()
    
    #站点类别数量
    sites_count = models.App_sites.query.count()

    #服务器数量
    servers_count = models.App_servers.query.count()

    #总更新次数
    update_count = models.App_deploy_node_task.query.count()
  
    #字典赋值
    count_dic['apps_count'] = apps_count
    count_dic['sites_count'] = sites_count
    count_dic['servers_count'] = servers_count
    count_dic['update_count'] = update_count

    #最近10次更新
    update_list = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.batch_no,
                                                              models.App_deploy_batch.id,
                                                              models.App_deploy_batch.subject,
                                                              models.App_deploy_batch.app_name,
                                                              models.App_deploy_batch.type,
                                                              models.App_deploy_batch.env,
                                                              models.App_deploy_batch.message_type,
                                                              models.App_deploy_batch.restart_tomcat,
                                                              models.App_deploy_batch.status,
                                                              models.App_deploy_batch.auditor,
                                                              models.App_deploy_batch.operator,
                                                              models.App_deploy_batch.message_cc,
                                                              models.App_deploy_batch.content,
                                                              models.App_deploy_batch.file_check,
                                                              models.App_deploy_batch.desc,
                                                              models.App_deploy_batch.file_check,
                                                              models.App_deploy_batch.before_command,
                                                              models.App_deploy_batch.after_command,
                                                              models.App_deploy_batch.create_time,
                                                              models.App_deploy_batch.finish_time,
                                                              models.App_deploy_batch.launcher,
                                                              models.Users_role.username).filter(
        models.App_deploy_batch.launcher == models.Users_role.account).order_by(
        desc(models.App_deploy_batch.create_time)).limit(10).all()

    # 项目更新次数Top10
    app_update_top10 = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.app_name,
                                                                   func.count(models.App_deploy_batch.id).label(
                                                                       'count')).group_by(
        models.App_deploy_batch.app_name).order_by(desc(func.count(models.App_deploy_batch.id))).limit(10).all()

    # 发起人更新次数Top10
    app_launcher_top10 = models.App_deploy_batch.query.with_entities(models.Users_role.username,
                                                                     models.App_deploy_batch.launcher,
                                                                     func.count(models.App_deploy_batch.id).label(
                                                                         'count')).filter(
        models.App_deploy_batch.launcher == models.Users_role.account).group_by(models.Users_role.username).order_by(
        desc(func.count(models.App_deploy_batch.id))).limit(10).all()

    #获取最近七天日期
    today = date.today()
    senven_day_list = []
    for i in range(0, 31):
        d2 = today + timedelta(-i)
        senven_day_list.append(d2.strftime("%m/%d"))

    #最近一个月整站更新次数
    full_update_list = [(a.date, a.count) for a in models.App_deploy_batch.query.with_entities(
        func.date_format(models.App_deploy_batch.create_time, '%m/%d').label('date'),
        func.count(models.App_deploy_batch.id).label('count')).filter(
        models.App_deploy_batch.type.in_((0, 2))).group_by(
        func.date_format(models.App_deploy_batch.create_time, '%m/%d'))]
    #列表转换成字典
    full_update_dict = dict(full_update_list)

    #最近一个月部分更新次数
    incre_update_list = [(a.date, a.count) for a in models.App_deploy_batch.query.with_entities(
        func.date_format(models.App_deploy_batch.create_time, '%m/%d').label('date'),
        func.count(models.App_deploy_batch.id).label('count')).filter(
        models.App_deploy_batch.type.in_((1, 3))).group_by(
        func.date_format(models.App_deploy_batch.create_time, '%m/%d'))]
    #列表转换成字典
    incre_update_dict = dict(incre_update_list)
    
    return render_template("site/index.html",
                           count_dic=count_dic,
                           update_list=update_list,
                           app_update_top10=app_update_top10,
                           app_launcher_top10=app_launcher_top10,
                           APP_ENV=g.config.get('APP_ENV'),
                           DEPLOY_STATUS=g.config.get('DEPLOY_STATUS'),
                           DEPLOY_TYPE=g.config.get('DEPLOY_TYPE'),
                           senven_day_list=senven_day_list,
                           full_update_dict=full_update_dict,
                           incre_update_dict=incre_update_dict)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    登录页面
    """
    # 如果已经认证过，则直接跳转首页
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('site.index'))

    form = LoginForm()

    # if form.validate_on_submit():
    if request.method == "POST":

        config = current_app.config

        # 查询登录用户是否有权限登录
        #user = Sys_Users_Role.query.filter(Sys_Users_Role.account == form.account.data,
        #                                   Sys_Users_Role.role_id > 0).first()

        # user = Users_role.query.filter(Users_role.account == form.account.data,
        #                                    Users_role.role_id > 0).first()
        user = Users_role.query.filter(Users_role.account == form.account.data,
                                       Users_role.role_id > 0).first()

        # 实例化utils.ldapHandle，连接好ldap，并准备好接受查询
        print "#"*20
        print user
        print "#"*20

        ldap_conn = openldap_conn_open()

        # 查询登录用户是否为管理用户并通过ldap验证
        if user is not None and ldap_conn.ldap_user_auth(uid=form.account.data, passwd=form.password.data):
            login_user(user, form.remember_me.data)
            session['account'] = user.account
            user_tag = config.get('USER_ROLES_TAG')[int(user.role_id)]
            session['user_tag'] = user_tag
            # app.logger.info('用户: %s 登录成功。' % form.account.data)

            # 关闭ldap连接
            ldap_conn.ldap_conn_close()

            # 获取用户IP
            headers_list = request.headers.getlist("X-Forwarded-For")
            user_real_ip = headers_list[0] if headers_list else request.remote_addr

            # 用户登录时间
            user.last_login_time = datetime.now()
            user.last_login_ip = user_real_ip

            # 写入数据库
            user.save()

            #保存用户操作记录
            user_ac_record = User_ac_log(uid=g.user.uid,
                                             account=g.user.account,
                                             ip=g.user_real_ip,
                                             action='login',
                                             result='True')
            # 写入数据库
            user_ac_record.save()

            return redirect(session.get('next_url') or url_for('site.index'))
        else:

            flash('用户名或密码错误！')

    return render_template('user/login.html', form=form)

@bp.route("/logout")
@login_required
def logout():
    """
    注销登录
    """

    # 保存用户操作记录
    user_ac_record = User_ac_log(uid=g.user.uid,
                                     account=g.user.account,
                                     ip=g.user_real_ip,
                                     action='logout',
                                     # ac_object=g.user.account,
                                     result='True')
    # 写入数据库
    user_ac_record.save()

    logout_user()

    session.pop('account', None)
    session.pop('user_tag', None)
    return redirect(url_for('site.login'))

#列出站点
@bp.route('/sites', methods=['GET', 'POST'])
@bp.route('/sites/<int:page>', methods=['GET', 'POST'])
@login_required
#@SAPermission()
def sites(page=1):
    form = SearchSiteForm()
    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        items = models.App_sites.query.filter('site_name' + filter_string).all()

        total = len(items)
        return render_template('site/sites.html', total=total, object_list=items, form=form)
    else:
        total = models.App_sites.query.count()
        # paginate = models.App_sites.query.order_by(models.App_sites.id).paginate(page, g.config.get('POSTS_PER_PAGE'),
        #                                                                          False)
        # paginate = models.App_sites.query.order_by(models.App_sites.id).paginate(page, g.config.get('POSTS_PER_PAGE'),
        #                                                                          False)
        # object_list = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.batch_no,
        #                                                           models.App_deploy_batch.id,
        #                                                           models.App_deploy_batch.subject,
        #                                                           models.App_deploy_batch.app_name,
        #                                                           models.App_deploy_batch.type,
        #                                                           models.Users.username).filter(
        #     models.App_deploy_batch.launcher == models.Users.account, 'app_name' + filter_string).order_by(
        #     desc(models.App_deploy_batch.create_time)).limit(20).all()
        paginate = models.App_sites.query.with_entities(models.App_sites.id,
                                                        models.App_sites.site_name,
                                                        models.App_sites.status,
                                                        models.App_sites.business_id,
                                                        # models.App_sites.business_name,
                                                        models.App_sites.create_time,
                                                        models.App_sites.flush_time,
                                                        models.Business.business_name).filter(
            models.App_sites.business_id == models.Business.id).order_by(
                models.App_sites.id).paginate(page, g.config.get('POSTS_PER_PAGE'), False)

        object_list = paginate.items

        pagination = models.App_sites.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        return render_template('site/sites.html', total=total, pagination=pagination, object_list=object_list, form=form)

#查询站点
@bp.route('/query', methods=['GET', 'POST'])
@bp.route('/query/<int:page>', methods=['GET', 'POST'])
@login_required
def l_sites(page=1):
    form = SearchSiteForm()
    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        items = models.App_sites.query.filter('site_name' + filter_string).all()

        total = len(items)
        return render_template('site/l_sites.html', total=total, object_list=items, form=form)
    else:
        total = models.App_sites.query.count()
        paginate = models.App_sites.query.order_by(models.App_sites.id).paginate(page, g.config.get('POSTS_PER_PAGE'),
                                                                                 False)
        object_list = paginate.items

        pagination = models.App_sites.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        return render_template('site/l_sites.html', total=total, pagination=pagination, object_list=object_list, form=form)


#树状显示页面
@bp.route('/t_sites', methods=['GET', 'POST'])
@login_required
def t_sites():
    return render_template('site/t_sites.html')


#树状显示查询接口
@bp.route('/sites_tree', methods=['GET', 'POST'])
@login_required
def sites_tree():
    action = request.args.get('action')

    # 判断是否有ajax请求
    if action == 'ajax':
        if request.form.get('id').isdigit():
            tree_id = int(request.form.get('id'))

            #如果是0，则是页面初始化
            if tree_id == 0:
                tree_source = models.App_sites.query.filter(models.App_sites.id.in_([1000, 2000, 2500, 3000, 4000, 4500, 5000, 6000, 6500, 7000, 8000, 8500])).all()

                tree_data = {"status": "OK", "data": []}
                for item in tree_source:
                    tree_data['data'].append({"id": item.id, "name": item.site_name, "type": "folder",
                                              "additionalParameters": {"id": item.id, "children": True}})
            #大类ID(1000,2000,3000)
            elif str(tree_id)[1:9] == "000":
                tree_source = models.App_sites.query.filter(models.App_sites.id.like(str(tree_id)[0] + '%'),
                                                            models.App_sites.id != tree_id).order_by(
                    models.App_sites.site_name).all()

                tree_data = {"status": "OK", "data": []}
                for item in tree_source:
                    tree_data['data'].append({"id": item.id, "name": item.site_name, "type": "folder",
                                              "additionalParameters": {"id": item.id, "children": True}})
            #站点类别id
            else:
                tree_source = models.Apps.query.with_entities(models.Apps.id, models.Apps.app_name).filter(
                    models.Apps.site == tree_id).order_by(models.Apps.app_name).all()

                tree_data = {"status": "OK", "data": []}
                for item in tree_source:
                    tree_data['data'].append({"id": item.app_name, "name": item.app_name, "type": "folder",
                                              "additionalParameters": {"id": item.app_name, "children": True}})
        else:
            #如果传递的是app_name，则应该是字符串
            tree_id = request.form.get('id')

            tree_source = models.App_nodes.query.with_entities(models.App_nodes.node_id,
                                                               models.App_nodes.node_ip).filter(
                models.App_nodes.app_name == tree_id).order_by(models.App_nodes.node_ip).all()

            tree_data = {"status": "OK", "data": []}
            for item in tree_source:
                tree_data['data'].append({"id": item.node_id, "name": item.node_ip, "type": "item",
                                          "additionalParameters": {"id": item.node_id, "children": False}})


    else:
        tree_data = {"status": "ERROR", "data": []}

    return json.dumps(tree_data)


#站点类别详情
@bp.route('/siteinfo/<int:id>', methods=['GET'])
@login_required
def siteinfo(id):
    form = AddSiteForm()
    form_sorce = models.App_sites.query.filter_by(id=int(id))[0]

    if request.method == "GET":
        form.site_name.data = form_sorce.site_name

        #获取该站点类别下的应用和部署节点
        items = models.App_nodes.query.with_entities(models.App_nodes.app_name,
                                                     func.group_concat(models.App_nodes.node_ip).label(
                                                         'node_list')).filter(models.Apps.id == models.App_nodes.app_id,
                                                                              models.Apps.site == id).group_by(
            models.App_nodes.app_name).all()
        total_app = len(items)
        #Tomcat实例数量
        total_instance = models.App_nodes.query.filter(models.Apps.id == models.App_nodes.app_id,
                                                       models.Apps.site == id).count()
        #部署节目数量
        total_node = models.App_nodes.query.filter(models.Apps.id == models.App_nodes.app_id,
                                                   models.Apps.site == id).group_by(models.App_nodes.node_ip).count()

    return render_template('site/siteinfo.html', form=form, object_list=items, total_app=total_app, total_node=total_node,
                           total_instance=total_instance)


#增加站点
@bp.route('/addsite', methods=['GET', 'POST'])
@login_required
@SAPermission()
def addsite():
    #构建一个添加应用表单
    form = AddSiteForm()

    # form_sorce = models.Business.query.filter_by(id=int(id))[0]

    #应用类别'前端', '后端', '后台'
    form.site_type.choices = [(item, g.config.get('APP_SITE_TYPE')[item]) for item in
                              range(len(g.config.get('APP_SITE_TYPE')))]

    # 数据库中选择业务类别
    form.business_id.choices = [(a.id, a.business_name) for a in \
                                models.Business.query.order_by(models.Business.business_name).all()]

    # form.business_name.choices = [(item, g.config.get('APP_SITE_TYPE')[item]) for item in
    #                           range(len(g.config.get('APP_SITE_TYPE')))]

    # 根据form选择的business_id去business表中查询到business_name的值
    businessname_db = models.Business.query.filter(models.Business.id == form.business_id.data).first()

    if request.method == "POST":
    # if form.validate_on_submit():

        #从当前数据库中获得相应类别最大ID+1,作为新增加类别id
        if form.site_type.data == 0:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 1000,
                    models.App_sites.id < 2000).first()[
                    0]
        elif form.site_type.data == 1:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 2000,
                    models.App_sites.id < 2500).first()[
                    0]
        elif form.site_type.data == 2:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 2500,
                    models.App_sites.id < 3000).first()[
                    0]
        elif form.site_type.data == 3:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 3000,
                    models.App_sites.id < 4000).first()[
                    0]
        elif form.site_type.data == 4:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 4000,
                    models.App_sites.id < 4500).first()[
                    0]
        elif form.site_type.data == 5:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 4500,
                    models.App_sites.id < 5000).first()[
                    0]
        elif form.site_type.data == 6:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 5000,
                    models.App_sites.id < 6000).first()[
                    0]
        elif form.site_type.data == 7:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 6000,
                    models.App_sites.id < 6500).first()[
                    0]
        elif form.site_type.data == 8:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 6500,
                    models.App_sites.id < 7000).first()[
                    0]
        elif form.site_type.data == 9:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 7000,
                    models.App_sites.id < 8000).first()[
                    0]
        elif form.site_type.data == 10:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 8000,
                    models.App_sites.id < 8500).first()[
                    0]
        elif form.site_type.data == 11:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 8500,
                    models.App_sites.id < 9000).first()[
                    0]

        elif form.site_type.data == 12:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 9000,
                    models.App_sites.id < 9500).first()[
                    0]

        elif form.site_type.data == 13:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 9500,
                    models.App_sites.id < 10000).first()[
                    0]

        elif form.site_type.data == 14:
            site_id = \
                models.App_sites.query.with_entities(func.max(models.App_sites.id) + 1).filter(
                    models.App_sites.id >= 10000,
                    models.App_sites.id < 10500).first()[
                    0]

        #通过表单构建数据库插入记录
        record = models.App_sites(id=site_id,
                                  site_name=g.config.get('APP_SITE_TYPE')[
                                                int(form.site_type.data)] + form.site_name.data,
                                  business_id=form.business_id.data,
                                  business_name=businessname_db.business_name,
                                  status=1)
        #写入数据库
        if record.save():
            flash('添加成功！')
            # 保存用户操作记录
            # user_ac_record = models.User_ac_log(uid=g.user.uid,
            #                                     account=g.user.account,
            #                                     ip=g.user_real_ip,
            #                                     action='addsite',
            #                                     result=record.site_name)
            # #写入数据库
            # user_ac_record.save()

        #重定向回应用页面
        return redirect(url_for('site.sites'))

    return render_template('site/addsite.html', form=form)

#编辑站点
@bp.route('/editsite/<int:id>', methods=['GET', 'POST'])
@login_required
#@SAPermission()
def editsite(id):
    form = AddSiteForm()
    form_sorce = models.App_sites.query.filter_by(id=int(id))[0]

    #数据库中选择业务类别
    form.business_id.choices = [(a.id, a.business_name) for a in \
                                    models.Business.query.order_by(models.Business.business_name).all()]

    if request.method == "GET":
        form.site_name.data = form_sorce.site_name
        # form.business_name.data = form_sorce.business_name




        form.business_id.data = form_sorce.business_id
        #获取该站点类别下的应用和部署节点
        items = models.App_nodes.query.with_entities(models.App_nodes.app_name,
                                                     func.group_concat(models.App_nodes.node_ip).label(
                                                         'node_list')).filter(models.Apps.id == models.App_nodes.app_id,
                                                                              models.Apps.site == id).group_by(
            models.App_nodes.app_name).all()
        total_app = len(items)
        #Tomcat实例数量
        total_instance = models.App_nodes.query.filter(models.Apps.id == models.App_nodes.app_id,
                                                       models.Apps.site == id).count()
        #部署节目数量
        total_node = models.App_nodes.query.filter(models.Apps.id == models.App_nodes.app_id,
                                                   models.Apps.site == id).group_by(models.App_nodes.node_ip).count()

    if request.method == "POST":
        form_sorce.site_name = form.site_name.data
        form_sorce.business_id = form.business_id.data
        # form_sorce.business_name = form.business_name.data

        if form_sorce.save():
            #app.logger.info(form_sorce.name + form_sorce.username)

            #保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='editsite',
                                                result=form_sorce.site_name
                                                )
            #写入数据库
            user_ac_record.save()

        return redirect(url_for('site.sites'))

    return render_template('site/editsite.html', form=form, object_list=items, total_app=total_app, total_node=total_node,
                           total_instance=total_instance)


#删除站点类别
#正式使用将关闭该功能，只允许编辑，不允许删除
@bp.route('/delsite/<int:id>', methods=['GET'])
@login_required
#@SAPermission()
def delsite(id):
    del_source = models.App_sites.query.filter_by(id=id).first_or_404()
    del_source.delete()
    return redirect(url_for('site.sites'))


#将站点类别状态置为停用
@bp.route('/onoffsite/<int:id>', methods=['GET'])
@login_required
#@SAPermission()
def onoffsite(id):
    source = models.App_sites.query.filter_by(id=id).first_or_404()
    if source.status == 1:
        source.status = 0
    else:
        source.status = 1
    source.save()
    return redirect(url_for('site.sites'))




@bp.route('/api/v1.0/node/modify', methods=['POST'])
def node_status_modify():
    """
    设置节点状态
    """
    if not request.json or not 'node_status' in request.json:
        abort(400)

    try:
        node = models.App_servers.query.filter_by(server_name=request.json['node_name']).first()

        if node:

            node.status = int(request.json['node_status'])
            if node.save():
                # 查询该ip上部署应用
                app_list = models.App_nodes.query.filter_by(node_ip=node.inner_ip).all()

                headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

                if node.status == 2:  # 暂时维护，切走流量
                    for app in app_list:
                        json_data = {"mode": "del", "appname": app.app_name.encode('utf8'), "usip": node.inner_ip.encode('utf8')}
                        post_return = requests.post(g.config.get('WAF_UPSTREAM_SET_RAM_API'), data=json.dumps(json_data),
                                      headers=headers)

                elif node.status in (3, 4):  # 下架，报废，切走流量和永久修改nginx upstream配置文件，移除并关闭tomcat
                    for app in app_list:
                        json_data = {"mode": "del", "appname": app.app_name.encode('utf8'), "usip": node.inner_ip.encode('utf8')}
                        #先切走流量后持久化到配置文件
                        requests.post(g.config.get('WAF_UPSTREAM_SET_RAM_API'), data=json.dumps(json_data),
                                      headers=headers)
                        requests.post(g.config.get('WAF_UPSTREAM_SET_FILE_API'), data=json.dumps(json_data),
                                      headers=headers)

                        # 删除应用部署节点
                        del_source = models.App_nodes.query.filter_by(app_name=app_name,
                                                                      node_ip=node.inner_ip).first_or_404()
                        del_source.delete()

                elif node.status == 1:  # 正常使用，恢复流量
                    for app in app_list:
                        json_data = {"mode": "add", "appname": app.app_name.encode('utf8'), "usip": node.inner_ip.encode('utf8')}
                        post_return = requests.post(g.config.get('WAF_UPSTREAM_SET_RAM_API'), data=json.dumps(json_data),
                                      headers=headers)


                # 获取用户IP
                headers_list = request.headers.getlist("X-Forwarded-For")
                user_real_ip = headers_list[0] if headers_list else request.remote_addr

                # 保存用户操作记录
                user_ac_record = models.User_ac_log(uid=0,
                                                    account='api',
                                                    ip=user_real_ip,
                                                    action='api_node_modify',
                                                    result=node.inner_ip + '/status:' + str(node.status))
                #写入数据库
                user_ac_record.save()

                return_data = {request.json['node_name']: {"result": 0,
                                                           "desc": "Success!"}}
            else:
                return_data = {request.json['node_name']: {"result": 1,
                                                           "desc": "Failed!"}}

        else:
            return_data = {request.json['node_name']: {"result": 1,
                                                       "desc": "This Node is not exist!"}}

    except:
        return_data = {request.json['node_name']: {"result": 1,
                                                   "desc": "Failed!"}}

    # json格式返回任务号和修改状态，返回码202
    response = make_response(jsonify(return_data))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 202


# 跨域接口post中转
@bp.route('/api/v1.0/ops_check/post/transit', methods=['POST'])
def ops_check_post_transit():
    url = request.json.get('url')
    json_data = request.json.get('json_data')
    try:
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        post_return = requests.post(url, data=json.dumps(json_data), headers=headers)
        post_result = post_return.json()
    except Exception, e:
        post_result = {"status": "ERROR"}
    return json.dumps(post_result), 202


@bp.route('/api/v1.0/node/status/<node_name>', methods=['GET'])
def node_status(node_name):
    """
    获取节点当前状态
    """
    try:
        node = models.App_servers.query.filter_by(server_name=node_name).first()
        node_status = node.status

    except:
        node_status = "Null"

    # json格式返回任务号和修改状态，返回码202
    response = make_response(jsonify({node_name: {'status': node_status}}))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 202


@bp.route('/api/v1.0/node/listapp/<node_name>', methods=['GET'])
def node_listapp(node_name):
    """
    获取节点部署应用
    """
    if node_name.lower() == 'all':
        node_app_list = models.App_servers.query.with_entities(models.App_servers.server_name,
                                                               models.Apps.app_name,
                                                               models.Apps.app_path,
                                                               models.Apps.tomcat_path,
                                                               models.Apps.port,
                                                               models.Apps.shutdown_port).filter(
            models.Apps.id == models.App_nodes.app_id,
            models.App_nodes.node_id == models.App_servers.id,
            models.App_servers.status == 1).all()

        node_app_data = {}
        for app_item in node_app_list:
            if not node_app_data.get(app_item.server_name):
                node_app_data[app_item.server_name.encode('utf8')] = []

            node_app_data[app_item.server_name.encode('utf8')].append(dict([("app_name", app_item.app_name),
                                                                            ("app_path", app_item.app_path),
                                                                            ("tomcat_path", app_item.tomcat_path),
                                                                            ("port", app_item.port),
                                                                            ("shutdown_port", app_item.shutdown_port)]))

    else:
        try:
            # 获取结点IP
            node = models.App_servers.query.filter_by(server_name=node_name).first()
            if node:
                node_app_list = models.Apps.query.with_entities(models.Apps.app_name,
                                                                models.Apps.app_path,
                                                                models.Apps.tomcat_path,
                                                                models.Apps.port,
                                                                models.Apps.shutdown_port).filter(
                    models.Apps.id == models.App_nodes.app_id,
                    models.App_nodes.node_id == node.id).all()

                if node_app_list:
                    node_app_data = {}
                    node_app_data[node_name.encode('utf8')] = []
                    for app_item in node_app_list:
                        node_app_data[node_name.encode('utf8')].append(dict([("app_name", app_item.app_name),
                                                                             ("app_path", app_item.app_path),
                                                                             ("tomcat_path", app_item.tomcat_path),
                                                                             ("port", app_item.port),
                                                                             (
                                                                                 "shutdown_port",
                                                                                 app_item.shutdown_port)]))

                else:
                    node_app_data = {node_name: {"result": 1, "desc": "This Node is not deploy any app!"}}
            else:
                node_app_data = {node_name: {"result": 1, "desc": "This Node is not exist!"}}

        except:
            node_app_data = {node_name: {"result": 1, "desc": "Error!"}}

    # json格式返回任务号和修改状态，返回码202
    response = make_response(jsonify(node_app_data))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response, 202


# Tomcat操作任务状态返回接口
#接口：修改更新任务状态
@bp.route('/api/v1.0/tomcat_task/modify_status/<task_no>', methods=['POST'])
#@csrf.exempt
def modify_tomcat_task_status(task_no):
    if not request.json or not 'status' in request.json:
        abort(400)

    #查询任务并修改任务状态
    record = models.App_tomcat_his.query.filter_by(task_no=task_no).first()
    record.status = int(request.json['status'])

    #如果是重启，将conclusion内容存入数据库，并写入完成时间
    if request.json.get('conclusion'):
        record.conclusion = request.json.get('conclusion')
        record.finish_time = datetime.now()

    if request.json.get('desc'):
        record.detail = request.json.get('desc')
        record.finish_time = datetime.now()

    record.save()

    #如果重启任务返回重启异常或重启成功，则检查是否还有重启任务没有完成，如果都完成了，则修改重启批次状态
    if record.status >= 2:
        #统计状态为排队中(0)和重启中(1)的任务数
        task_count = models.App_tomcat_his.query.filter(models.App_tomcat_his.batch_no == record.batch_no,
                                                              models.App_tomcat_his.status <= 1).count()

        #如果更新任务都操作完成了，则修改批次状态为对应状态
        if int(task_count) == 0:
            batch = models.App_tomcat_restart.query.filter_by(batch_no=record.batch_no).first_or_404()
            #任务状态为重启异常(2),批次状态为重启异常(5)
            if record.status == 2:
                batch.status = 5
            #任务状态为重启成功(3),批次状态为重启成功(4)
            elif record.status == 3:
                batch.status = 4

            batch.finish_time = datetime.now()
            batch.save()

    #json格式返回任务号和修改状态，返回码202
    return jsonify({'task_no': task_no, 'status': record.status}), 202


#接口：修改更新任务状态
# @csrf.exempt
@bp.route('/api/v1.0/test/<task_no>', methods=['POST'])
def task_status(task_no):
    return task_no
    # print "bbbb"*20


#接口：修改更新任务状态
@bp.route('/api/v1.0/node_task/modify_status/<task_no>', methods=['POST'])
# @csrf.exempt
def modify_node_task_status(task_no):
    print "bbbb"*20
    print request.json
    if not request.json or not 'status' in request.json:
        abort(400)

    #查询任务并修改任务状态
    record = models.App_deploy_node_task.query.filter_by(task_no=task_no).first()
    print "xxx"*20
    print record.status
    record.status = int(request.json['status'])

    #如果更新结束，将conclusion内容存入数据库，并写入完成时间
    if request.json.get('conclusion'):
        record.conclusion = request.json.get('conclusion')
        record.finish_time = datetime.now()

    if request.json.get('desc'):
        record.detail = request.json.get('desc')
        record.finish_time = datetime.now()

    record.save()

    #如果更新任务返回更新异常或更新成功，则检查是否还有更新任务没有完成，如果都完成了，则修改更新批次状态
    if record.status >= 2:
        #统计状态为排队中(0)和更新中(1)的任务数
        task_count = models.App_deploy_node_task.query.filter(models.App_deploy_node_task.batch_no == record.batch_no,
                                                              models.App_deploy_node_task.status <= 1).count()
        #如果更新任务都操作完成了，则修改批次状态为对应状态
        if int(task_count) == 0:
            batch = models.App_deploy_batch.query.filter_by(batch_no=record.batch_no).first_or_404()
            #任务状态为更新异常(2),批次状态为更新异常(5)
            if record.status == 2:
                batch.status = 5
            #任务状态为更新成功(3),批次状态为更新成功(4)
            elif record.status == 3:
                batch.status = 4
            batch.finish_time = datetime.now()
            batch.save()

            ##发送消息通知
            receiver_list = []
            receiver_list.append(batch.launcher)
            receiver_list.append(batch.operator)
            #如果有需要抄送的帐号
            if batch.message_cc:
                for cc_account in batch.message_cc.split(','):
                    receiver_list.append(cc_account)
            mes = Mess(receiver_list=receiver_list, mes_content=batch.batch_no + '更新完成', ext_info=batch.batch_no)
            mes.sendInstationMes()
            #邮件通知
            if batch.message_type == 1 or batch.message_type == 3:
                mes.sendEmail()


    #json格式返回任务号和修改状态，返回码202
    return jsonify({'task_no': task_no, 'status': record.status}), 202


#用户行为日志查询
@bp.route('/ac_logs', methods=['GET', 'POST'])
@bp.route('/ac_logs/<int:page>', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def ac_logs(page=1):
    form = SearchSiteForm()

    if request.method == "POST":
        filter_string = '%' + form.s_content.data + '%'
        object_list = models.User_ac_log.query.with_entities(models.Users.username,
                                                             models.User_ac_log.create_time,
                                                             models.User_ac_log.action,
                                                             models.User_ac_log.result,
                                                             models.User_ac_log.ip).filter(
            models.User_ac_log.uid == models.Users.uid,
            or_((models.Users.account.like(filter_string)),
                (models.Users.username.like(filter_string)))).order_by(desc(models.User_ac_log.create_time)).limit(
            50).all()

        return render_template('site/ac_logs.html', object_list=object_list, form=form,
                               USER_ACTION_CONVERT=g.config.get('USER_ACTION_CONVERT'))
    else:

        total = models.User_ac_log.query.count()
        paginate = models.User_ac_log.query.with_entities(models.Users.username,
                                                          models.User_ac_log.create_time,
                                                          models.User_ac_log.action,
                                                          models.User_ac_log.result,
                                                          models.User_ac_log.ip).filter(
            models.User_ac_log.uid == models.Users.uid).order_by(desc(models.User_ac_log.create_time)).paginate(page,
                                                                                                                g.config.get(
                                                                                                                    'POSTS_PER_PAGE'),
                                                                                                                False)
        object_list = paginate.items

        pagination = models.User_ac_log.query.with_entities(models.Users.username,
                                                            models.User_ac_log.create_time,
                                                            models.User_ac_log.action,
                                                            models.User_ac_log.result,
                                                            models.User_ac_log.ip).filter(
            models.User_ac_log.uid == models.Users.uid).paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))

    return render_template('site/ac_logs.html', total=total, object_list=object_list, form=form, pagination=pagination,
                           USER_ACTION_CONVERT=g.config.get('USER_ACTION_CONVERT'))







# #添加站点权限
# @bp.route('/addsiterole', methods=['GET', 'POST'])
# #@login_required
# #@SAPermission()
# def addsiterole():
#     #构建一个添加站点权限表单
#     form = AddSiteRoleForm()
#
#     # 数据库中选择站点类别
#     form.site_id.choices = [(a.id, a.site_name) for a in \
#                                 models.App_sites.query.order_by(models.App_sites.site_name).all()]
#
#     # 数据库中选择USER-ID
#     form.user_id.choices = [(a.id, a.username) for a in \
#                                 models.Users.query.order_by(models.Users.id).all()]
#
#     if form.validate_on_submit():
#         #通过表单构建数据库插入记录
#         record = models.App_sites(user_id=form.user_id.data,
#                                       id=form.site_id.data)
#         #写入数据库
#         if record.save():
#             flash('站点权限添加成功！')
#
#             #保存用户操作记录
#            # user_ac_record = models.User_action_log(uid=g.user.uid,
#             #                                    account=g.user.account,
#             #                                    ip=g.user_real_ip,
#             #                                    action='addserver',
#             #                                    result=record.inner_ip)
#             #写入数据库
#             #user_ac_record.save()
#
#         #重定向回应用页面
#         return redirect(url_for('site.roles'))
#
#     return render_template('site/addsite_role.html', form=form)
