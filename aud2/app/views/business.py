# coding: utf-8
__author__ = 'lancger'

import json
from flask import render_template, request, redirect, url_for, Blueprint, flash, g, \
    session, current_app
from .. import models
from flask.ext.login import login_user, logout_user, login_required
from datetime import datetime, date, timedelta
from ..forms import LoginForm, SearchSiteForm, SearchServerForm, SearchAppForm, SearchBusinessForm, AddBusinessForm, AddBusinessRoleForm
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users
from ..permissions import UserPermission, DeveloperPermission, AuditorPermission, SAPermission, AdminPermission
from sqlalchemy import desc, func
from ..utils.qredis import RedisTools
from ..utils.ldap_handle import openldap_conn_open
from ..utils.ldap_sync_user import ldapConnOpen, ldapHandle
# from ..permissions import SSPermission

bp = Blueprint('business', __name__)



#查询站点
@bp.route('/query', methods=['GET', 'POST'])
@bp.route('/query/<int:page>', methods=['GET', 'POST'])
@login_required
def l_business(page=1):
    form = SearchBusinessForm()
    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        items = models.Business.query.filter('business_name' + filter_string).all()

        total = len(items)
        return render_template('business/l_business.html', total=total, object_list=items, form=form)
    else:
        total = models.Business.query.count()
        paginate = models.Business.query.order_by(models.Business.id).paginate(page, g.config.get('POSTS_PER_PAGE'),
                                                                                 False)
        object_list = paginate.items

        pagination = models.Business.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        return render_template('business/l_business.html', total=total, pagination=pagination, object_list=object_list, form=form)





#列出服务器(普通用户权限)
@bp.route('/l_apps', methods=['GET', 'POST'])
@bp.route('/l_apps/<int:page>', methods=['GET', 'POST'])
#@app.route('/l_apps', methods=['GET', 'POST'])
#@app.route('/l_apps/<int:page>', methods=['GET', 'POST'])
@login_required
def l_apps(page=1):
    form = SearchAppForm()
    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        #filter_field = 'a.' + form.s_select.data

        ##创建数据库连接
        #engine = create_engine(g.config.get('SQLALCHEMY_DATABASE_URI'))
        #metadata = MetaData(bind=engine, reflect=True)
        #conn = engine.connect()
        #with conn:
        #    sql = text(
        #        "select a.*,b.node_list,c.site_name from apps a left join (select app_id,group_concat(node_ip) node_list from app_nodes group by app_id) b on a.id=b.app_id join app_sites c on c.id=a.site where %s like %s" % (
        #        filter_field, filter_string))
        #    #获取应用配置和节点部署数据
        #    result = conn.execute(sql)
        #
        #    object_list = []
        #    for row in result:
        #        object_list.append(dict(row))

        object_list = [row._asdict() for row in models.Apps.query.with_entities(models.Apps.id,
                                                                                models.Apps.app_name,
                                                                                models.Apps.status,
                                                                                models.Apps.app_path,
                                                                                models.Apps.tomcat_path,
                                                                                models.Apps.port,
                                                                                models.Apps.shutdown_port,
                                                                                models.Apps.site,
                                                                                models.Apps.beta_server,
                                                                                models.Apps.rsync_path_name,
                                                                                models.Apps.desc,
                                                                                models.App_sites.site_name,
                                                                                func.group_concat(
                                                                                    models.App_nodes.node_ip).label(
                                                                                    'node_list')).outerjoin(
            models.App_nodes,
            models.App_nodes.app_id == models.Apps.id).join(
            models.App_sites, models.App_sites.id == models.Apps.site).filter(
            form.s_select.data + filter_string).group_by(models.Apps.id).all()]

        total = len(object_list)

        return render_template('business/l_apps.html', total=total, object_list=object_list, form=form)
    else:
        ##创建数据库连接
        #engine = create_engine(g.config.get('SQLALCHEMY_DATABASE_URI'))
        #metadata = MetaData(bind=engine, reflect=True)
        #conn = engine.connect()
        #with conn:
        #    #获取应用配置和节点部署数据
        #    result = conn.execute(
        #        'select a.*,b.node_list,c.site_name from apps a left join (select app_id,group_concat(node_ip) node_list from app_nodes group by app_id) b on a.id=b.app_id join app_sites c on c.id=a.site')
        #
        #    object_list = []
        #    for row in result:
        #        object_list.append(dict(row))

        object_list = [row._asdict() for row in models.Apps.query.with_entities(models.Apps.id,
                                                                                models.Apps.app_name,
                                                                                models.Apps.status,
                                                                                models.Apps.app_path,
                                                                                models.Apps.tomcat_path,
                                                                                models.Apps.port,
                                                                                models.Apps.shutdown_port,
                                                                                models.Apps.site,
                                                                                models.Apps.rsync_path_name,
                                                                                models.Apps.desc,
                                                                                models.App_sites.site_name,
                                                                                func.group_concat(
                                                                                    models.App_nodes.node_ip).label(
                                                                                    'node_list')).outerjoin(
            models.App_nodes,
            models.App_nodes.app_id == models.Apps.id).join(
            models.App_sites, models.App_sites.id == models.Apps.site).group_by(models.Apps.id).all()]



        #for row in result:
        #    print row
        #    print row.__dict__
        #    object_list.append(row.__dict__)

        total = len(object_list)

        #获取Tomcat部署实例数量
        tomcat_count = models.App_nodes.query.count()

        return render_template('business/l_apps.html', total=total, object_list=object_list, form=form,
                               tomcat_count=tomcat_count)


#列出站点
# @bp.route('/business', methods=['GET', 'POST'])
# @bp.route('/business/<int:page>', methods=['GET', 'POST'])
# #@login_required
# #@SAPermission()
# def business(page=1):
#     form = SearchBusinessForm()
#     if request.method == "POST":
#         filter_string = ' like "%' + form.s_content.data + '%"'
#         items = models.Business.query.filter('name' + filter_string).all()
#
#         total = len(items)
#         return render_template('business/business.html', total=total, object_list=items, form=form)
#     else:
#         # total = models.App_sites.query.count()
#         total = models.Business.query.count()
#         paginate = models.Business.query.order_by(models.Business.id).paginate(page, g.config.get('POSTS_PER_PAGE'),
#                                                                                  False)
#         object_list = paginate.items
#         print "%%"*20
#         print object_list
#         pagination = models.Business.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
#         return render_template('business/business.html', total=total, pagination=pagination, object_list=object_list, form=form)


#列出业务
@bp.route('/list', methods=['GET', 'POST'])
# @bp.route('/list/<int:page>', methods=['GET', 'POST'])
@login_required
#@SAPermission()
def business():
    page = 1
    form = SearchBusinessForm()
    redistools = RedisTools()
    redis_ip = request.args.get('redis_ip')
    # if request.method == "POST":
    if redis_ip:
        print ""
        print "aa"
        # filter_string = ' like "%' + form.s_content.data + '%"'
        # items = models.Business.query.filter('site_name' + filter_string).all()
        #
        # total = len(items)
        # return render_template('business/business.html', total=total, object_list=items, form=form)

        print "***" * 20
        print redis_ip
        print "***" * 20
        dbinfo = models.Business.query.filter(models.Business.redis_ip == redis_ip).first()

        if not dbinfo:
            return 'Redis 服务不存在！'
        values = redistools.qkeys(redis_ip, dbinfo.redis_port, dbinfo.redis_db)

        return json.dumps(values, indent=4).replace('\n','<br>').replace(' ','&nbsp;')

    else:
        total = models.Business.query.count()
        pagination = models.Business.query.order_by(models.Business.id).paginate(page, g.config.get('POSTS_PER_PAGE'),
                                                                                 False)
        object_list = pagination.items

        redis_dict = {}



        for item in object_list:
            values = redistools.qkeys(item.redis_ip, item.redis_port, item.redis_db)
            # print values
            redis_dict[item.redis_ip] = values
        # print redis_dict

        # pagination = models.Business.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        return render_template('business/business.html', total=total, redis_dict=redis_dict, object_list=object_list, form=form)

#添加业务类别
@bp.route('/addbusiness', methods=['GET', 'POST'])
@login_required
@AdminPermission()
#def addserver():
def addbusiness():
    #构建一个添加业务表单
    form = AddBusinessForm()

    # #服务器位置，0 公司机房，1 广州七星岗电信，2 广州沙溪电信，3 北京北显联通，4 深圳龙岗电信，5 阿里云杭州
    # form.location.choices = [(item, g.config.get('SERVER_LOCATION')[item]) for item in
    #                          range(len(g.config.get('SERVER_LOCATION')))]
    # #类别：0 测试环境，1 beta环境，2 生产环境
    # form.env.choices = [(item, g.config.get('APP_ENV')[item]) for item in range(len(g.config.get('APP_ENV')))]
    # #服务器类型，0 物理机，1，KVM虚拟机，2 LXC容器
    # form.type.choices = [(item, g.config.get('SERVER_TYPE')[item]) for item in range(len(g.config.get('SERVER_TYPE')))]
    #
    # #服务器状态，(0 务器准备中',1'正常运行中',2'维护中',3'已下架',4'已报废')
    # form.status.choices = [(item, g.config.get('SERVER_STATUS')[item]) for item in range(len(g.config.get('SERVER_STATUS')))]
    #
    #
    # #业务选择，(0 彩票业务, 1 金融业务 , 2 滴滴业务， 3 配资业务， 4 新增业务)
    # form.business_id.choices = [(item, g.config.get('BUSSINESS_TYPE')[item]) for item in range(len(g.config.get('BUSSINESS_TYPE')))]

    if form.validate_on_submit():
        #通过表单构建数据库插入记录
        record = models.Business(business_name=form.business_name.data,
                                    desc=form.desc.data,
                                    beta_ip=form.beta_ip.data,
                                    redis_ip=form.redis_ip.data,
                                    redis_port=form.redis_port.data,
                                    redis_db=form.redis_db.data)
        #写入数据库
        if record.save():
            flash('业务添加成功！')

            #保存用户操作记录
           # user_ac_record = models.User_action_log(uid=g.user.uid,
            #                                    account=g.user.account,
            #                                    ip=g.user_real_ip,
            #                                    action='addserver',
            #                                    result=record.inner_ip)
            #写入数据库
            #user_ac_record.save()

        #重定向回应用页面
        return redirect(url_for('business.business'))

    return render_template('business/addbusiness.html', form=form)


# #编辑业务
# @bp.route('/editbusiness/<int:id>', methods=['GET', 'POST'])
# #@login_required
# #@SAPermission()
# def editbusiness(id):
#     form = AddBusinessForm()
#     form_sorce = models.Business.query.filter_by(id=int(id))[0]
#
#     if request.method == "GET":
#         form.name.data = form_sorce.name
#
#         #获取该站点类别下的应用和部署节点
#         items = models.Business.query.query.filter_by(id=int(id))
#
#
#     if request.method == "POST":
#         form_sorce.name = form.name.data
#
#         if form_sorce.save():
#             #app.logger.info(form_sorce.name + form_sorce.username)
#
#             #保存用户操作记录
#             user_ac_record = models.User_ac_log(uid=g.user.uid,
#                                                 account=g.user.account,
#                                                 ip=g.user_real_ip,
#                                                 action='editbusiness',
#                                                 result=form_sorce.name)
#             #写入数据库
#             user_ac_record.save()
#
#         return redirect(url_for('business.business'))
#
#     return render_template('business/editbusiness.html', form=form, object_list=items)

#编辑业务
@bp.route('/editbusiness/', methods=['GET', 'POST'])
@bp.route('/editbusiness/<int:id>', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def editbusiness(id=0):
    form = AddBusinessForm()

    form_sorce = models.Business.query.filter_by(id=int(id))[0]

    if request.method == "GET":
        form.business_name.data = form_sorce.business_name
        form.desc.data = form_sorce.desc
        form.beta_ip.data = form_sorce.beta_ip
        form.redis_ip.data = form_sorce.redis_ip
        form.redis_port.data = form_sorce.redis_port
        form.redis_db.data = form_sorce.redis_db
        items = models.Business.query.all()
        total = len(items)

    if request.method == "POST":
        form_sorce.business_name = form.business_name.data
        form_sorce.desc = form.desc.data
        form_sorce.beta_ip = form.beta_ip.data
        form_sorce.redis_ip = form.redis_ip.data
        form_sorce.redis_port = form.redis_port.data
        form_sorce.redis_db = form.redis_db.data

        if form_sorce.save():
            print "wcwcwc-------------"
            flash("成功修改业务")
            # app.logger.info(form_sorce.name + form_sorce.username)

            #保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='editserver',
                                                result=form_sorce.business_name)
            #写入数据库
            user_ac_record.save()
            print "hhhhh-------------"


        return redirect(url_for('business.business'))

    return render_template('business/editbusiness.html', form=form, object_list=items, total=total)


#列出业务权限
@bp.route('/roles', methods=['GET', 'POST'])
@bp.route('/roles/<int:page>', methods=['GET', 'POST'])
@login_required
@SAPermission()
def roles(page=1):
    form = SearchBusinessForm()
    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        items = models.User_business.query.filter('username' + filter_string).all()
        total = len(items)
        return render_template('business/business_roles.html', total=total, object_list=items, form=form)
    else:
        total = models.User_business.query.count()
        # paginate = models.User_business.query.order_by(models.User_business.username).paginate(page, g.config.get(
        #     'POSTS_PER_PAGE'), False)

        paginate = models.User_business.query.with_entities(models.User_business.id,
                                                            models.User_business.user_id,
                                                            models.User_business.username,
                                                            models.User_business.business_id,
                                                            models.User_business.business_name,
                                                            models.User_business.create_time,
                                                            models.User_business.flush_time).order_by(
            models.User_business.id).paginate(page, g.config.get('POSTS_PER_PAGE'), False)
        object_list = paginate.items

        pagination = models.User_business.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        return render_template('business/business_roles.html', total=total, pagination=pagination, object_list=object_list,
                               form=form)

        #
        #
        # total = models.Site_roles.query.count()
        #
        # paginate = models.Site_roles.query.with_entities(models.Site_roles.id,
        #                                                  models.Site_roles.user_id,
        #                                                  models.Site_roles.username,
        #                                                  models.Site_roles.site_id,
        #                                                  # models.App_sites.business_name,
        #                                                  models.Site_roles.site_name,
        #                                                  models.Site_roles.business_id,
        #                                                  models.Site_roles.business_name,
        #                                                  models.Site_roles.create_time,
        #                                                  models.Site_roles.flush_time, ).order_by(
        #     models.Site_roles.id).paginate(page, g.config.get('POSTS_PER_PAGE'), False)
        #
        # object_list = paginate.items
        #
        # pagination = models.Site_roles.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        # return render_template('site/app_roles.html', total=total, pagination=pagination, object_list=object_list,
        #                        form=form)

        #
    # else:
    #     total = models.User_business.query.count()
    #     paginate = models.User_business.query.with_entities(models.User_business.username). \
    #         filter(models.User_business.business_id == models.Business.id,
    #                models.User_business.user_id == models.Users.id).paginate(page, g.config.get(
    #         'POSTS_PER_PAGE'), False)
    #
    #     object_list = paginate.items
    #
    #     pagination = models.Business.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
    #     return render_template('business/business_roles.html', total=total, pagination=pagination,
    #                            object_list=object_list,
    #                            form=form)

        # 任务拆分
        # nodes = models.App_nodes.query.with_entities(models.App_nodes.id, models.App_nodes.node_ip). \
        #     filter(models.App_nodes.node_id == models.App_servers.id,
        #            models.App_nodes.app_id == deploy_batch.app_id,
        #            models.App_servers.env == deploy_batch.env).all()
    # paginate = models.User_business.query.order_by(models.User_business.username).paginate(page, g.config.get('POSTS_PER_PAGE'), False)
    #
    # object_list = paginate.items
    #
    # pagination = models.User_business.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
    #
    # # return render_template('business/business_roles.html', object_list=object_list)
    #
    # return render_template('business/business_roles.html', pagination=pagination, object_list=object_list,)


#编辑业务权限
@bp.route('/editroles/', methods=['GET', 'POST'])
@bp.route('/editroles/<int:id>', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def editroles(id=0):
    form = AddBusinessForm()

    form_sorce = models.Business.query.filter_by(id=int(id))[0]

    if request.method == "GET":
        form.business_name.data = form_sorce.business_name
        form.desc.data = form_sorce.desc
        form.beta_ip.data = form_sorce.beta_ip
        form.redis_ip.data = form_sorce.redis_ip
        form.redis_port.data = form_sorce.redis_port
        form.redis_db.data = form_sorce.redis_db
        items = models.Business.query.all()
        total = len(items)

    if request.method == "POST":
        form_sorce.business_name = form.business_name.data
        form_sorce.desc = form.desc.data
        form_sorce.beta_ip = form.beta_ip.data
        form_sorce.redis_ip = form.redis_ip.data
        form_sorce.redis_port = form.redis_port.data
        form_sorce.redis_db = form.redis_db.data

        if form_sorce.save():
            print "wcwcwc-------------"
            flash("成功修改业务")
            # app.logger.info(form_sorce.name + form_sorce.username)

            #保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='editserver',
                                                result=form_sorce.business_name)
            #写入数据库
            user_ac_record.save()
            print "hhhhh-------------"


        return redirect(url_for('business.business'))

    return render_template('business/editbusiness.html', form=form, object_list=items, total=total)

#添加业务权限
@bp.route('/addbusinessrole', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def addbusinessrole():
    #构建一个添加业务表单
    form = AddBusinessRoleForm()

    # if form.validate_on_submit():
    if request.method == "POST":
        #校验同一用户名和对应的权限只能有一条记录
        if models.User_business.query.filter(models.User_business.user_id==form.user_id.data,models.User_business.business_id==form.business_id.data).first():
            flash("账户权限已存在！")
            return redirect(url_for('business.roles'))
        #根据form选择的user_id去获取到username字段的值
        username_db = models.Users.query.filter(models.Users.id == form.user_id.data).first()

        #判断用户存不存在
        if not username_db:
            flash("用户不存在")
        #根据form选择的business_id去business表中查询到business_name的值
        businessname_db = models.Business.query.filter(models.Business.id == form.business_id.data).first()

        # 通过表单构建数据库插入记录
        record = models.User_business(user_id=form.user_id.data,
                                      username=username_db.username,
                                      business_id=form.business_id.data,
                                      business_name=businessname_db.business_name)
        # 写入数据库
        if record.save():
            flash('业务权限添加成功！')

            # 保存用户操作记录
            # user_ac_record = models.User_action_log(uid=g.user.uid,
            #                                    account=g.user.account,
            #                                    ip=g.user_real_ip,
            #                                    action='addserver',
            #                                    result=record.inner_ip)
            # 写入数据库
            # user_ac_record.save()

        # 重定向回应用页面
        return redirect(url_for('business.roles'))

    # 数据库中选择业务类别
    form.business_id.choices = [(a.id, a.business_name) for a in \
                                models.Business.query.order_by(models.Business.business_name).all()]

    # 数据库中选择USER-ID
    form.user_id.choices = [(a.id, a.username) for a in \
                                models.Users.query.order_by(models.Users.id).all()]


    return render_template('business/addbusiness_role.html', form=form)


#删除业务权限
#正式使用将关闭该功能，只允许编辑，不允许删除
@bp.route('/delbusinessrole/<int:id>', methods=['GET'])
@login_required
@AdminPermission()
def delbusinessrole(id):
    del_source = models.User_business.query.filter_by(user_id=id).first_or_404()
    del_source.delete()
    return redirect(url_for('business.roles'))
