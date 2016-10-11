# coding: utf-8
__author__ = 'lancger'

from datetime import datetime, timedelta
import hashlib, json,os
from .. import models
from flask import render_template, request, redirect, url_for, Blueprint, flash, abort, g, \
    session, current_app
from flask.ext.login import login_required
from sqlalchemy import text, or_, and_, asc, desc, func, distinct, create_engine, MetaData, exists
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users, Site_roles
from ..forms import SearchAppForm, AddAppForm, AddAppNodeForm, SearchAppRoleForm, AddSiteRoleForm
from ..utils.ldap_handle import openldap_conn_open, ad_conn_open
from ..utils.sms import gen_sms_vcode, send_sms, shadow_phone
from ..permissions import UserPermission, DeveloperPermission, AuditorPermission, SAPermission, AdminPermission

bp = Blueprint('self', __name__)



#列出应用
@bp.route('/app', methods=['GET', 'POST'])
@bp.route('/app/<int:page>', methods=['GET', 'POST'])
@login_required
#@SAPermission()
def app(page=1):
    form = SearchAppForm()
    #服务器位置，0 公司机房，1 广州七星岗电信，2 广州沙溪电信，3 北京北显联通，4 深圳龙岗电信，5 阿里云杭州
    # form.location.choices = [(item, g.config.get('SERVER_LOCATION')[item]) for item in
    #                              range(len(g.config.get('SERVER_LOCATION')))]
    #业务类别  0 彩票业务', 1'金融业务', 2'滴滴业务', 3'配资业务', 4'新增业务

    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        filter_field = form.s_select.data
        items = models.Apps.query.filter(filter_field + filter_string).all()

        #通过枚举重新修改对象列表的对应的值
        for item in items:
            item.site = models.App_sites.query.with_entities(models.App_sites.site_name).filter(
                models.App_sites.id == int(item.site)).first()[0]

        total = len(items)
        return render_template('self/app.html', total=total, object_list=items, form=form, BUSSINESS_TYPE=g.config.get('BUSSINESS_TYPE'))
    else:
        total = models.Apps.query.count()
        # print "#"*20
        # print total
        # print "#"*20
        paginate = models.Apps.query.order_by(models.Apps.port).paginate(page, g.config.get('POSTS_PER_PAGE'), False)
        object_list = paginate.items

        #通过枚举重新修改对象列表的对应的值
        for item in object_list:
            # print "#"*20
            #print item.site
            #print int(item.site).first()[0]
            print "#"*20
            #item.site = models.db.session.query(models.App_sites, models.Business).filter(models.App_sites.business_id == models.Business.id).first()
            #item.site = db.session.query(Assets, Server).filter(Server.server_hostname == node_name, Assets.assets_id == Server.server_assets_id).first()

            # #OK的获取站点类别
            # item.site = models.App_sites.query.with_entities(models.App_sites.site_name).filter(
            #     models.App_sites.id == int(item.site)).first()[0]
            item.site = models.App_sites.query.with_entities(models.App_sites.site_name).filter(
                models.App_sites.id == int(item.site)).first()[0]

            # item = models.db.session.query(models.App_sites,models.Apps).filter(models.App_sites.id == models.Apps.site).first()[]
            # form.site_name.data = item.App_sites.site_name

            print "#"*20
            print item.id
            print "#"*20

        pagination = models.Apps.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        return render_template('self/app.html', total=total, pagination=pagination, object_list=object_list, form=form, BUSSINESS_TYPE=g.config.get('BUSSINESS_TYPE'))



#应用详情
@bp.route('/appdetail/', methods=['GET', 'POST'])
@bp.route('/appdetail/<int:appid>', methods=['GET'])
@login_required
def appdetail(appid=0):
    if appid == 0 and request.args.get('app_name'):
        app_name = request.args.get('app_name')
        obj_sorce = models.Apps.query.filter_by(app_name=app_name)[0]
    else:
        obj_sorce = models.Apps.query.filter_by(id=int(appid))[0]

    obj_sorce.site = models.App_sites.query.with_entities(models.App_sites.site_name).filter(
        models.App_sites.id == obj_sorce.site).first()[0]

    if request.method == "GET":
        #该应用所部署的节点
        items = models.App_nodes.query.with_entities(models.App_nodes.node_ip,
                                                     models.App_servers.env.label('env_id'),
                                                     models.App_servers.env,
                                                     models.App_servers.status). \
            filter(models.App_nodes.node_id == models.App_servers.id,
                   models.App_nodes.app_id == obj_sorce.id).order_by(models.App_nodes.node_ip).all()
        total = len(items)

        # 该应用更新历史
        deploy_history = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.batch_no,
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
                                                                     models.App_deploy_batch.is_undo,
                                                                     models.App_deploy_batch.file_check,
                                                                     models.App_deploy_batch.desc,
                                                                     models.App_deploy_batch.file_check,
                                                                     models.App_deploy_batch.before_command,
                                                                     models.App_deploy_batch.after_command,
                                                                     models.App_deploy_batch.create_time,
                                                                     models.App_deploy_batch.finish_time,
                                                                     models.Users.username).filter(
            models.App_deploy_batch.launcher == models.Users.account,
            models.App_deploy_batch.app_id == obj_sorce.id).order_by(
            desc(models.App_deploy_batch.create_time)).limit(10).all()

    return render_template('self/appdetail.html', object_list=items, total=total, appid=appid, obj=obj_sorce,
                           APP_ENV=g.config.get('APP_ENV'), deploy_history=deploy_history,
                           DEPLOY_STATUS=g.config.get('DEPLOY_STATUS'), DEPLOY_TYPE=g.config.get('DEPLOY_TYPE'))




#应用配置和节点列表json接口

#比对更新发布系统中各项目所配置的应用服务器，和nginx实际配置upstream server比较测试
@bp.route('/checkupstream/', methods=['GET'])
@login_required
@SAPermission()
def checkupstream():
    #执行检查文件列表脚本，并输出到stdout
    stdout = os.popen(g.config.get('APP_UPSTREAM_CHECK_SCRIPT'))
    check_data = ''.join(stdout.readlines())
    stdout.close()

    #回车符和空格替换
    check_data = check_data.replace('\n', '<br>').replace(' ', '&nbsp')

    return check_data


#比对更新发布系统中各项目所配置的应用服务器，连接IP和应用端口测试
@bp.route('/checkrealserver/', methods=['GET'])
@login_required
@SAPermission()
def checkrealserver():
    #执行检查文件列表脚本，并输出到stdout
    stdout = os.popen(g.config.get('APP_REAL_SERVER_CHECK_SCRIPT'))
    check_data = ''.join(stdout.readlines())
    stdout.close()

    #回车符和空格替换
    check_data = check_data.replace('\n', '<br>').replace(' ', '&nbsp')

    return check_data


#增加应用配置
@bp.route('/addapp', methods=['GET', 'POST'])
@login_required
@SAPermission()
def addapp():
    #构建一个添加应用表单
    form = AddAppForm()

    #站点类别的选择
    form.site.choices = [(a.id, a.site_name) for a in models.App_sites.query.order_by(models.App_sites.id)]

    #form.beta_server.choices = [(g.config.get('BETA_SERVER')[item], g.config.get('BETA_SERVER')[item]) for item in
    #                            range(len(g.config.get('BETA_SERVER')))]

    # #业务类别
    # form.business_id.choices = [(item, g.config.get('BUSSINESS_TYPE')[item]) for item in
    #                             range(len(g.config.get('BUSSINESS_TYPE')))]
    #数据库中选择业务类别
    form.business_id.choices = [(a.id, a.business_name) for a in \
                                    models.Business.query.order_by(models.Business.business_name).all()]
    # #业务类别(这样写其实是有问题的)
    # form.business_id.choices = [(g.config.get('BUSSINESS_TYPE')[item], g.config.get('BUSSINESS_TYPE')[item]) for item in
    #                             range(len(g.config.get('BUSSINESS_TYPE')))]
    # #rsync名称
    # form.rsync_path_name.choices = [(g.config.get('RSYNC_PATH_NAME')[item], g.config.get('RSYNC_PATH_NAME')[item]) for
    #                                 item in range(len(g.config.get('RSYNC_PATH_NAME')))]
    #刚开始的写法
    # form.rsync_path_name.choices = [(g.config.get('RSYNC_PATH_NAME')[item], g.config.get('RSYNC_PATH_NAME')[item]) for item in range(len(g.config.get('RSYNC_PATH_NAME')))]

    #rsync名称（不报错是因为，在models中定义的这个字段为str类型。但现在改成int类型了# ）
    form.rsync_path_name.choices = [(item, g.config.get('RSYNC_PATH_NAME')[item]) for item in range(len(g.config.get('RSYNC_PATH_NAME')))]
    print "+" * 20
    #if form.validate_on_submit():
    if request.method == "POST":
        print "#" * 20
        print form.rsync_path_name.data
        #通过表单构建数据库插入记录
        record = models.Apps(app_name=form.app_name.data.strip(),
                             status=1,
                             app_path=form.app_path.data.strip(),
                             tomcat_path=form.tomcat_path.data.strip(),
                             port=form.port.data.strip(),
                             site=form.site.data,
                             shutdown_port=form.shutdown_port.data.strip(),
                             business_id=form.business_id.data,
                             rsync_path_name=form.rsync_path_name.data,
                             desc=form.desc.data)
        #写入数据库
        if record.save():
            flash('添加项目成功！')
        #写入数据库
        # if record.save():
        #     #保存用户操作记录
        #     user_ac_record = models.User_ac_log(uid=g.user.uid,
        #                                         account=g.user.account,
        #                                         ip=g.user_real_ip,
        #                                         action='addapp',
        #                                         result=record.app_name)
        #     #写入数据库
        #     user_ac_record.save()

        #重定向回应用页面
        return redirect(url_for('self.app'))
    return render_template('self/addapp.html', form=form)

#编辑应用
@bp.route('/editapp/', methods=['GET', 'POST'])
@bp.route('/editapp/<int:appid>', methods=['GET', 'POST'])
@login_required
@SAPermission()
def editapp(appid=0):
    form = AddAppForm()

    if appid == 0 and request.args.get('app_name'):
        app_name = request.args.get('app_name')
        print app_name
        form_sorce = models.Apps.query.filter_by(app_name=app_name)[0]
    else:
        form_sorce = models.Apps.query.filter_by(id=int(appid))[0]
        print "uuu"*20
        print form_sorce.business_id
        print "uuu"*20

    if request.method == "GET":
        form.app_name.data = form_sorce.app_name
        form.status.data = form_sorce.status
        form.app_path.data = form_sorce.app_path
        form.tomcat_path.data = form_sorce.tomcat_path
        form.port.data = form_sorce.port
        form.shutdown_port.data = form_sorce.shutdown_port
        form.site.data = form_sorce.site
        form.desc.data = form_sorce.desc
        form.svn_url.data = form_sorce.svn_url
        form.business_id.data = form_sorce.business_id
        #form.rsync_path_name.data = form_sorce.rsync_path_name
        form.rsync_path_name.data = g.config.get('RSYNC_PATH_NAME')[form_sorce.rsync_path_name]
        print "111"*20
        print form_sorce.rsync_path_name
        print form.rsync_path_name.data

        #应用类别
        form.site.choices = [(a.id, a.site_name) for a in models.App_sites.query.order_by(models.App_sites.id)]

        # #业务类别
        # form.business_id.choices = [(item, g.config.get('BUSSINESS_TYPE')[item]) for item in
        #                         range(len(g.config.get('BUSSINESS_TYPE')))]


        #数据库中选择业务类别
        form.business_id.choices = [(a.id, a.business_name) for a in \
                                    models.Business.query.order_by(models.Business.business_name).all()]

        # form.beta_server.choices = [(g.config.get('BETA_SERVER')[item], g.config.get('BETA_SERVER')[item]) for item in
        #                             range(len(g.config.get('BETA_SERVER')))]

        #form.rsync_path_name.choices = [(g.config.get('RSYNC_PATH_NAME')[item], g.config.get('RSYNC_PATH_NAME')[item])
        #                                for item in range(len(g.config.get('RSYNC_PATH_NAME')))]
        #form.rsync_path_name.choices = [(g.config.get('RSYNC_PATH_NAME')[item], g.config.get('RSYNC_PATH_NAME')[item])
        #                                for item in range(len(g.config.get('RSYNC_PATH_NAME')))]

        #rsync名称（不报错是因为，在models中定义的这个字段为str类型。但现在改成int类型了# ）
        form.rsync_path_name.choices = [(item, g.config.get('RSYNC_PATH_NAME')[item]) for item in \
                                    range(len(g.config.get('RSYNC_PATH_NAME')))]

        #该应用所部署的节点
        items = models.App_nodes.query.with_entities(models.App_nodes.node_id,
                                                     models.App_nodes.node_ip,
                                                     models.App_servers.env.label('env_id'),
                                                     models.App_servers.env,
                                                     models.App_servers.status). \
            filter(models.App_nodes.node_id == models.App_servers.id,
                   models.App_nodes.app_id == form_sorce.id).order_by(models.App_nodes.node_ip).all()
        total = len(items)

        #通过枚举重新修改对象列表的对应的值
        #for item in items:
        #    #类别：0 测试环境，1 beta环境，2 生产环境
        #    item.env = APP_ENV[int(item.env)]

        add_node_form = AddAppNodeForm()

        ##创建数据库连接
        #engine = create_engine(g.config.get('SQLALCHEMY_DATABASE_URI'))
        #metadata = MetaData(bind=engine, reflect=True)
        #conn = engine.connect()
        #with conn:
        #    #允许增加的节点IP，需要先排除当前已经增加了的
        #    add_node_form.node_ip.choices = [(a.inner_ip, a.inner_ip) for a in conn.execute(
        #        'select inner_ip from app_servers where inner_ip not in (select node_ip from app_nodes where app_id=%s) order by env,inner_ip',
        #        form_sorce.id)]

        #允许增加的节点IP，需要先排除当前已经增加了的
        add_node_form.node_ip.choices = [(a.inner_ip, a.inner_ip) for a in models.App_servers.query.filter(
            ~exists().where(and_(models.App_nodes.node_ip == models.App_servers.inner_ip,
                                 models.App_nodes.app_id == form_sorce.id)),
                                 models.App_servers.business_id == form_sorce.business_id,
                                 models.App_servers.status == 1).order_by(
            models.App_servers.env, models.App_servers.inner_ip)]

    if request.method == "POST":
        form_sorce.app_name = form.app_name.data.strip()
        form_sorce.status = form.status.data
        form_sorce.app_path = form.app_path.data.strip()
        form_sorce.tomcat_path = form.tomcat_path.data.strip()
        form_sorce.port = form.port.data.strip()
        form_sorce.shutdown_port = form.shutdown_port.data.strip()
        form_sorce.site = form.site.data
        form_sorce.desc = form.desc.data
        form_sorce.svn_url = form.svn_url.data
        form_sorce.business_id = form.business_id.data
        form_sorce.rsync_path_name = form.rsync_path_name.data

        rsync_path_name = request.args.get('rsync_path_name')
        print "/////////////"
        print form.rsync_path_name.data
        print "/////////////"
        if form_sorce.save():
            #app.logger.info(form_sorce.name + form_sorce.username)

            #保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='editapp',
                                                result=form_sorce.app_name)
            #写入数据库
            user_ac_record.save()

        return redirect(url_for('self.app'))

    return render_template('self/editapp.html', form=form, object_list=items, total=total, add_node_form=add_node_form,
                           appid=appid, APP_ENV=g.config.get('APP_ENV'))



# #编辑应用
# @bp.route('/editapp/', methods=['GET', 'POST'])
# @bp.route('/editapp/<int:appid>', methods=['GET', 'POST'])
# #@login_required
# #@SAPermission()
# def editapp(appid=0):
#     form = AddAppForm()
#
#     if appid == 0 and request.args.get('app_name'):
#         app_name = request.args.get('app_name')
#         form_sorce = models.Apps.query.filter_by(app_name=app_name)[0]
#
#     else:
#         form_sorce = models.Apps.query.filter_by(id=int(appid))[0]
#
#     if request.method == "GET":
#         form.app_name.data = form_sorce.app_name
#         form.status.data = form_sorce.status
#         form.app_path.data = form_sorce.app_path
#         form.tomcat_path.data = form_sorce.tomcat_path
#         form.port.data = form_sorce.port
#         form.shutdown_port.data = form_sorce.shutdown_port
#         form.site.data = form_sorce.site
#         form.desc.data = form_sorce.desc
#         form.svn_url.data = form_sorce.svn_url
#         form.business_id.data = form_sorce.business_id
#         form.rsync_path_name.data = form_sorce.rsync_path_name
#
#         #应用类别
#         form.site.choices = [(a.id, a.site_name) for a in models.App_sites.query.order_by(models.App_sites.id)]
#
#         #业务类别
#         form.business_id.choices = [(item, g.config.get('BUSSINESS_TYPE')[item]) for item in
#                                 range(len(g.config.get('BUSSINESS_TYPE')))]
#
#
#          #rsync名称（不报错是因为，在models中定义的这个字段为str类型。但现在改成int类型了# ）
#         form.rsync_path_name.choices = [(item, g.config.get('RSYNC_PATH_NAME')[item]) for item in range(len(g.config.get('RSYNC_PATH_NAME')))]
#         # form.rsync_path_name.choices = [(g.config.get('RSYNC_PATH_NAME')[item], g.config.get('RSYNC_PATH_NAME')[item])
#         #                                 for item in range(len(g.config.get('RSYNC_PATH_NAME')))]
#
#         #该应用所部署的节点
#         items = models.App_nodes.query.with_entities(models.App_nodes.node_id,
#                                                      models.App_nodes.node_ip,
#                                                      models.App_servers.env.label('env_id'),
#                                                      models.App_servers.env,
#                                                      models.App_servers.status). \
#             filter(models.App_nodes.node_id == models.App_servers.id,
#                    models.App_nodes.app_id == form_sorce.id).order_by(models.App_nodes.node_ip).all()
#         total = len(items)
#
#         #通过枚举重新修改对象列表的对应的值
#         #for item in items:
#         #    #类别：0 测试环境，1 beta环境，2 生产环境
#         #    item.env = APP_ENV[int(item.env)]
#
#         add_node_form = AddAppNodeForm()
#
#         ##创建数据库连接
#         #engine = create_engine(g.config.get('SQLALCHEMY_DATABASE_URI'))
#         #metadata = MetaData(bind=engine, reflect=True)
#         #conn = engine.connect()
#         #with conn:
#         #    #允许增加的节点IP，需要先排除当前已经增加了的
#         #    add_node_form.node_ip.choices = [(a.inner_ip, a.inner_ip) for a in conn.execute(
#         #        'select inner_ip from app_servers where inner_ip not in (select node_ip from app_nodes where app_id=%s) order by env,inner_ip',
#         #        form_sorce.id)]
#
#         #允许增加的节点IP，需要先排除当前已经增加了的
#         add_node_form.node_ip.choices = [(a.inner_ip, a.inner_ip) for a in models.App_servers.query.filter(
#             ~exists().where(and_(models.App_nodes.node_ip == models.App_servers.inner_ip,
#                                  models.App_nodes.app_id == form_sorce.id)),
#                                  models.App_servers.status == 1).order_by(
#             models.App_servers.env, models.App_servers.inner_ip)]
#
#     if request.method == "POST":
#         form_sorce.app_name = form.app_name.data.strip()
#         form_sorce.status = form.status.data
#         form_sorce.app_path = form.app_path.data.strip()
#         form_sorce.tomcat_path = form.tomcat_path.data.strip()
#         form_sorce.port = form.port.data.strip()
#         form_sorce.shutdown_port = form.shutdown_port.data.strip()
#         form_sorce.site = form.site.data
#         form_sorce.desc = form.desc.data
#         form_sorce.svn_url = form.svn_url.data
#         form_sorce.business_id = form.business_id.data
#         form_sorce.rsync_path_name = form.rsync_path_name.data
#
#         if form_sorce.save():
#             app.logger.info(form_sorce.name + form_sorce.username)
#
#             #保存用户操作记录
#             user_ac_record = models.User_ac_log(uid=g.user.uid,
#                                                 account=g.user.account,
#                                                 ip=g.user_real_ip,
#                                                 action='editapp',
#                                                 result=form_sorce.app_name)
#             #写入数据库
#             user_ac_record.save()
#
#         return redirect(url_for('self.app'))
#
#     return render_template('self/editapp.html', form=form, object_list=items, total=total, add_node_form=add_node_form,
#                            appid=appid, APP_ENV=g.config.get('APP_ENV'))


#将站点类别状态置为停用
@bp.route('/onoffapp/<int:id>', methods=['GET'])
@login_required
@SAPermission()
def onoffapp(id):
    source = models.Apps.query.filter_by(id=id).first_or_404()
    if source.status == 1:
        source.status = 0
    else:
        source.status = 1
    source.save()
    return redirect(url_for('self.app'))


#删除应用节点
@bp.route('/delappnode/', methods=['GET'])
@login_required
@SAPermission()
def delappnode():
    del_source = models.App_nodes.query.filter_by(app_id=request.args.get("app_id"),
                                                  node_ip=request.args.get("node_ip")).first_or_404()
    if del_source.delete():
        #保存用户操作记录
        user_ac_record = models.User_ac_log(uid=g.user.uid,
                                            account=g.user.account,
                                            ip=g.user_real_ip,
                                            action='delappnode',
                                            result=del_source.app_name + '-' + del_source.node_ip)
        #写入数据库
        user_ac_record.save()

    return redirect(url_for('self.editapp', appid=int(request.args.get("app_id"))))

#删除应用
@bp.route('/delapp/<int:id>', methods=['GET'])
@login_required
@SAPermission()
def delapp(id):
    del_source = models.Apps.query.filter_by(id=id).first_or_404()
    del_source.delete()
    return redirect(url_for('self.app'))


#给应用增加部署节点
@bp.route('/addappnode', methods=['POST'])
@login_required
#@SAPermission()
def addappnode():
    print "==================================="
    print "this is addappnode"
    node_id = models.App_servers.query.filter_by(inner_ip=request.form.get("node_ip"))[0].id

    print node_id
    record = models.App_nodes(
        app_id=request.form.get("app_id"),
        app_name=request.form.get("app_name"),
        node_ip=request.form.get("node_ip"),
        business_id=request.form.get("business_id"),
        node_id=node_id)
    if record.save():
        flash('添加成功！')
        # 保存用户操作记录
        # user_ac_record = models.User_ac_log(uid=g.user.uid,
        #                                     account=g.user.account,
        #                                     ip=g.user_real_ip,
        #                                     action='addappnode',
        #                                     result=record.app_name + '-' + record.node_ip)
        # #写入数据库
        # user_ac_record.save()

    return redirect(url_for('self.editapp', appid=int(request.form.get("app_id"))))




# #列出站点
# @bp.route('/sites', methods=['GET', 'POST'])
# @bp.route('/sites/<int:page>', methods=['GET', 'POST'])
# #@login_required
# #@SAPermission()
# def sites(page=1):
#     form = SearchSiteForm()
#     if request.method == "POST":
#         filter_string = ' like "%' + form.s_content.data + '%"'
#         items = models.App_sites.query.filter('site_name' + filter_string).all()
#
#         total = len(items)
#         return render_template('site/sites.html', total=total, object_list=items, form=form)
#     else:
#         total = models.App_sites.query.count()
#
#         paginate = models.App_sites.query.with_entities(models.App_sites.id,
#                                                         models.App_sites.site_name,
#                                                         models.App_sites.status,
#                                                         models.App_sites.business_id,
#                                                         # models.App_sites.business_name,
#                                                         models.App_sites.create_time,
#                                                         models.App_sites.flush_time,
#                                                         models.Business.business_name).filter(
#             models.App_sites.business_id == models.Business.id).order_by(
#                 models.App_sites.id).paginate(page, g.config.get('POSTS_PER_PAGE'), False)
#
#         object_list = paginate.items
#
#         pagination = models.App_sites.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
#         return render_template('site/sites.html', total=total, pagination=pagination, object_list=object_list, form=form)

#列出项目权限
@bp.route('/roles', methods=['GET', 'POST'])
@bp.route('/roles/<int:page>', methods=['GET', 'POST'])
@login_required
#@AdminPermission()
def roles(page=1):
    form = SearchAppRoleForm()
    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        items = models.Site_roles.query.filter('username' + filter_string).all()

        total = len(items)
        return render_template('site/app_roles.html', total=total, object_list=items, form=form)
    else:
        total = models.Site_roles.query.count()

        paginate = models.Site_roles.query.with_entities(models.Site_roles.id,
                                                                models.Site_roles.user_id,
                                                                models.Site_roles.username,
                                                                models.Site_roles.site_id,
                                                                # models.App_sites.business_name,
                                                                models.Site_roles.site_name,
                                                                models.Site_roles.business_id,
                                                                models.Site_roles.business_name,
                                                                models.Site_roles.create_time,
                                                                models.Site_roles.flush_time).order_by(
                models.Site_roles.id).paginate(page, g.config.get('POSTS_PER_PAGE'), False)

        object_list = paginate.items

        pagination = models.Site_roles.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        return render_template('site/app_roles.html', total=total, pagination=pagination, object_list=object_list, form=form)

        #
        # object_list = models.Site_roles.query.order_by(models.Site_roles.id).all()
        #
        #
        # return render_template('site/app_roles.html', object_list=object_list, form=form)


#删除项目权限
#正式使用将关闭该功能，只允许编辑，不允许删除
@bp.route('/delroles/<int:id>', methods=['GET'])
@login_required
@SAPermission()
def delsite(id):
    del_source = models.Site_roles.query.filter_by(user_id=id).first_or_404()
    del_source.delete()
    return redirect(url_for('self.roles'))



#添加业务权限
@bp.route('/addsiterole', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def addsiterole():
    #构建一个添加业务表单
    form = AddSiteRoleForm()
    #为了避免冗余查询，将post查询提前到# 数据库中选择站点类别 之前

    # if form.validate_on_submit():
    if request.method == "POST":
        #校验同一用户名和对应站点项目的权限只能有一条记录
        if models.Site_roles.query.filter(models.Site_roles.user_id==form.user_id.data,models.Site_roles.site_id==form.site_id.data).first():
            flash("账户对应的站点项目权限已存在！")

            # 重定向回应用页面
            return redirect(url_for('self.roles'))

        # 根据form选择的user_id去获取到username字段的值
        username_db = models.Users.query.filter(models.Users.id == form.user_id.data).first()

        #判断用户存不存在
        if not username_db:
            flash("用户不存在")

        #根据form选择的site_id去site_roles表中查询到的site_name值
        sitename_db = models.App_sites.query.filter(models.App_sites.id == form.site_id.data).first()

        print "---------------"*5
        print form.site_id.data

        print sitename_db.site_name
        print "---------------"*5

        # #根据form选择的site_id去app_sites表中查询到business_name的值
        # businessname_db = models.Business.query.filter(models.Business.id == form.business_id.data).first()
        businessname_db = models.App_sites.query.filter(models.App_sites.id == form.site_id.data).first()

        #根据选择的site_id去app_sites表中查询到business_name的值
        # businessname_db = models.Business.query.filter(models.Business.id == form.business_id.data).first()
        businessid_db = models.Business.query.filter(models.Business.business_name == businessname_db.business_name).first()

        # 通过表单构建数据库插入记录
        record = models.Site_roles(user_id=form.user_id.data,
                                   username=username_db.username,
                                   site_id=form.site_id.data,
                                   site_name=sitename_db.site_name,
                                   business_name=businessname_db.business_name,
                                   business_id=businessid_db.id
                                   )
        # 写入数据库
        if record.save():
            flash('项目权限添加成功！')

            # 保存用户操作记录
            # user_ac_record = models.User_action_log(uid=g.user.uid,
            #                                    account=g.user.account,
            #                                    ip=g.user_real_ip,
            #                                    action='addserver',
            #                                    result=record.inner_ip)
            # 写入数据库
            # user_ac_record.save()

        # 重定向回应用页面
        return redirect(url_for('self.roles'))

    # 数据库中选择站点类别
    form.site_id.choices = [(a.id, a.site_name) for a in \
                                models.App_sites.query.order_by(models.App_sites.id).all()]

    # 数据库中选择USER-ID
    form.user_id.choices = [(a.id, a.username) for a in \
                                models.Users.query.order_by(models.Users.id).all()]


    return render_template('self/addsite_role.html', form=form)
