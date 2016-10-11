# coding: utf-8
__author__ = 'lancger'

from datetime import datetime, timedelta
import hashlib, json,os
from .. import models
from flask import render_template, request, redirect, url_for, Blueprint, flash, abort, g, \
    session, current_app
from flask.ext.login import login_required
from ..utils.redisqueue import RedisQueue
from ..utils.message import Mess
from sqlalchemy import text, or_, and_, asc, desc, func, distinct, create_engine, MetaData, exists
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users, Site_roles
from ..forms import SearchAppForm, AddRestartForm, AddAppNodeForm
from ..utils.ldap_handle import openldap_conn_open, ad_conn_open
from ..utils.sms import gen_sms_vcode, send_sms, shadow_phone
from ..permissions import UserPermission, DeveloperPermission, AuditorPermission, SAPermission, AdminPermission



bp = Blueprint('tomcat', __name__)



#Tomcat操作任务
@bp.route('/tomcat_task/', methods=['GET', 'POST'])
# @bp.route('/tomcat_task/<node_id>', methods=['GET', 'POST'])
@login_required
@SAPermission()
def tomcat_task():
    queue_name = 'Tomcat1'

    if request.method == "POST":
        node_list = request.form.getlist('cb')
        action = request.form.get('btn')
        app_id = request.form.get('app_id')

        # 调试输出
        print node_list
        print action

        app = models.Apps.query.filter_by(id=app_id).first_or_404()

        # 设置type值：部署(0)，移除(1)，重启(2),tomcat打包(3),app打包(4),app部署(5),app和tomcat同时部署(6)
        if action == 'deploy':
            type = 0

        elif action == 'reboot':
            type = 2

        elif action == 'remove':
            type = 1

        elif action == 'appdeploy':
            type = 5

        elif action == 'tomcat_app_deploy':
            type = 6

        node_ip = node_list[0]
        # 根据传入的node_ip去查找这台服务器属于哪个业务
        app_server_attrs = models.App_servers.query.filter_by(inner_ip=node_ip).first_or_404()

        # 获取redis相关信息
        redis_attrs = models.Business.query.filter_by(id=app_server_attrs.business_id).first()


        # 根据节点列表，提交任务
        for node in node_list:
            app_node = models.App_nodes.query.filter_by(app_id=app.id, node_ip=node).first_or_404()

            # 应用tomcat重启批次前缀
            batch_no_prefix = "TC-"

            # 生成batch_no,strip去掉首尾空格
            batch_no = batch_no_prefix + app.app_name.strip() + "-" + datetime.now().strftime(
                '%Y%m%d%H%M%S')

            # 生成task_no
            task_no = 'TC-' + app.app_name.strip() + '-' + app_node.node_ip.replace('.',
                                                                                    '-') + '-' + datetime.now().strftime(
                '%Y%m%d%H%M%S')

            # 删除应用部署节点
            if type == 1:
                del_source = models.App_nodes.query.filter_by(app_id=app.id, node_ip=app_node.node_ip).first_or_404()
                del_source.delete()

            # 通过表单构建节点部署记录表插入记录
            record = models.App_tomcat_his(batch_no=batch_no,
                                           task_no=task_no,
                                           app_id=app.id,
                                           app_name=app.app_name,
                                           create_time=datetime.now(),
                                           node_id=app_node.node_id,
                                           node_ip=app_node.node_ip,
                                           app_path=app.app_path,
                                           tomcat_path=app.tomcat_path,
                                           status=0,  # 状态为排队中
                                           port=app.port,
                                           type=type)
            # 写入数据库
            if record.save():
                # 如果写入成功，任务加入redis队列
                # 构建一个加入队列json数据
                task_dic = {
                    "batch_no":record.batch_no,
                    "task_no": record.task_no,
                    "app_name": record.app_name.strip(),
                    "app_path": record.app_path.strip(),
                    "tomcat_path": record.tomcat_path.strip(),
                    "tomcat_port": record.port,
                    "node_ip": record.node_ip.strip(),
                    "type": record.type,
                    "beta_server": redis_attrs.beta_ip,
                    # "beta_server": app.beta_server,
                    # "rsync_path_name": app.rsync_path_name
                    # "rsync_path_name": g.config.get('RSYNC_PATH_NAME')[app_attrs.rsync_path_name]
                    "rsync_path_name": "www"

                }
                task_json = json.dumps(task_dic, skipkeys=True)

                # #增加任务到Redis队列
                # q = RedisQueue(queue_name, host=g.config.get('REDIS_HOST'), port=g.config.get('REDIS_PORT'),
                #                db=g.config.get('REDIS_DB'))
                # q.put(task_json)

                # 增加任务到Redis队列
                q = RedisQueue(queue_name, host=redis_attrs.redis_ip, port=redis_attrs.redis_port, db=redis_attrs.redis_db)
                q.put(task_json)

                # 保存用户操作记录
                user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                    account=g.user.account,
                                                    ip=g.user_real_ip,
                                                    action='tomcat_task',
                                                    result=record.app_name + '-' + record.node_ip)
                # 写入数据库
                user_ac_record.save()

        return redirect(url_for('tomcat.his'))

    node_id = request.args.get('node_id')
    # 根据传入的node_ip去查找这台服务器属于哪个业务
    app_server_attrs = models.App_servers.query.filter_by(id=node_id).first_or_404()

    # 获取redis相关信息
    redis_attrs = models.Business.query.filter_by(id=app_server_attrs.business_id).first()

    print app_server_attrs.business_id
    print redis_attrs.id

    # 根据业务，使用不同的Redis队列
    if app_server_attrs.business_id == 1 and redis_attrs.id == 1:
        host = redis_attrs.redis_ip
        port = redis_attrs.redis_port
        db = redis_attrs.redis_db
        beta_server = redis_attrs.beta_ip
        # queue_name = 'Tomcat1'

    elif app_server_attrs.business_id == 2 and redis_attrs.id == 2:
        host = redis_attrs.redis_ip
        port = redis_attrs.redis_port
        db = redis_attrs.redis_db
        beta_server = redis_attrs.beta_ip
        # queue_name = 'Tomcat1'

    elif app_server_attrs.business_id == 3 and redis_attrs.id == 3:
        host = redis_attrs.redis_ip
        port = redis_attrs.redis_port
        db = redis_attrs.redis_db
        beta_server = redis_attrs.beta_ip
        # queue_name = 'Tomcat1'

    elif app_server_attrs.business_id == 4 and redis_attrs.id == 4:
        host = redis_attrs.redis_ip
        port = redis_attrs.redis_port
        db = redis_attrs.redis_db
        beta_server = redis_attrs.beta_ip
        # queue_name = 'Tomcat1'


    #通过GET方式是处理单条数据
    #接收2个参数，节点id和应用ID
    node_id = request.args.get('node_id')
    app_id = request.args.get('app_id')

    #type：部署(0)，移除(1)，重启(2),打包(3)
    type = request.args.get('type')

    app = models.Apps.query.filter_by(id=app_id).first_or_404()
    node = models.App_nodes.query.filter_by(app_id=app.id, node_id=node_id).first_or_404()

    #生成task_no
    task_no = 'TC-' + app.app_name.strip() + '-' + node.node_ip.replace('.', '-') + '-' + datetime.now().strftime(
        '%Y%m%d%H%M%S')

    #通过表单构建节点部署记录表插入记录
    record = models.App_tomcat_his(task_no=task_no,
                                   app_id=app.id,
                                   app_name=app.app_name,
                                   create_time=datetime.now(),
                                   node_id=node.node_id,
                                   node_ip=node.node_ip,
                                   app_path=app.app_path,
                                   tomcat_path=app.tomcat_path,
                                   status=0,  #状态为排队中
                                   port=app.port,
                                   type=type)
    #写入数据库
    if record.save():
        #如果写入成功，任务加入redis队列
        #构建一个加入队列json数据
        task_dic = {
            "task_no": record.task_no,
            "app_name": record.app_name.strip(),
            "app_path": record.app_path.strip(),
            "tomcat_path": record.tomcat_path.strip(),
            "tomcat_port": record.port,
            "node_ip": record.node_ip.strip(),
            "type": record.type,
            # "beta_server": app.beta_server,
            "beta_server": redis_attrs.beta_ip,
            # "rsync_path_name": app.rsync_path_name
            "rsync_path_name": "www"
        }
        task_json = json.dumps(task_dic, skipkeys=True)

        # #增加任务到Redis队列
        # q = RedisQueue(queue_name, host=g.config.get('REDIS_HOST'), port=g.config.get('REDIS_PORT'),
        #                db=g.config.get('REDIS_DB'))
        # q.put(task_json)

        # 增加任务到Redis队列
        q = RedisQueue(queue_name, host=host, port=port, db=db)
        q.put(task_json)

        #保存用户操作记录
        user_ac_record = models.User_ac_log(uid=g.user.uid,
                                            account=g.user.account,
                                            ip=g.user_real_ip,
                                            action='tomcat_task',
                                            result=record.app_name + '-' + record.node_ip)
        #写入数据库
        user_ac_record.save()

    return redirect(url_for('tomcat.his'))


#Tomcat操作历史
@bp.route('/his/', methods=['GET', 'POST'])
@bp.route('/his/<int:page>', methods=['GET', 'POST'])
@login_required
@SAPermission()
def his(page=1):
    form = SearchAppForm()

    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        object_list = models.App_tomcat_his.query.filter('app_name' + filter_string).order_by(
            desc(models.App_tomcat_his.create_time)).limit(20).all()

        return render_template('tomcat/tomcat.html', object_list=object_list, form=form,
                               TOMCAT_OPERATION_TYPE=g.config.get('TOMCAT_OPERATION_TYPE'),
                               TOMCAT_OPERATION_STATUS=g.config.get('TOMCAT_OPERATION_STATUS'))
    else:
        paginate = models.App_tomcat_his.query.order_by(desc(models.App_tomcat_his.create_time)).paginate(page,
                                                                                                          g.config.get(
                                                                                                              'POSTS_PER_PAGE'),
                                                                                                          False)
        object_list = paginate.items
        total = len(object_list)

        pagination = models.App_tomcat_his.query.order_by(desc(models.App_tomcat_his.create_time)).paginate(page,
                                                                                                            per_page=g.config.get(
                                                                                                                'POSTS_PER_PAGE'))

        return render_template('tomcat/tomcat.html', object_list=object_list, form=form, pagination=pagination, total=total,
                               TOMCAT_OPERATION_TYPE=g.config.get('TOMCAT_OPERATION_TYPE'),
                               TOMCAT_OPERATION_STATUS=g.config.get('TOMCAT_OPERATION_STATUS'))



#Tomcat操作历史
@bp.route('/restart/', methods=['GET', 'POST'])
@bp.route('/restart/<int:page>', methods=['GET', 'POST'])
@login_required
@SAPermission()
def restart(page=1):
    form = SearchAppForm()

    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        object_list = models.App_tomcat_his.query.filter('app_name' + filter_string).order_by(
            desc(models.App_tomcat_his.create_time)).limit(20).all()

        return render_template('tomcat/restart_tomcat.html', object_list=object_list, form=form,
                               TOMCAT_OPERATION_TYPE=g.config.get('TOMCAT_OPERATION_TYPE'),
                               TOMCAT_OPERATION_STATUS=g.config.get('TOMCAT_OPERATION_STATUS'))
    else:
        paginate = models.App_tomcat_his.query.order_by(desc(models.App_tomcat_his.create_time)).paginate(page,
                                                                                                          g.config.get(
                                                                                                              'POSTS_PER_PAGE'),
                                                                                                          False)
        object_list = paginate.items
        total = len(object_list)

        pagination = models.App_tomcat_his.query.order_by(desc(models.App_tomcat_his.create_time)).paginate(page,
                                                                                                            per_page=g.config.get(
                                                                                                                'POSTS_PER_PAGE'))

        return render_template('tomcat/restart_tomcat.html', object_list=object_list, form=form, pagination=pagination,
                               total=total,
                               TOMCAT_OPERATION_TYPE=g.config.get('TOMCAT_OPERATION_TYPE'),
                               TOMCAT_OPERATION_STATUS=g.config.get('TOMCAT_OPERATION_STATUS'))

@bp.route('/node_list',methods=['POST'])
#@csrf.exempt
def node_list():
    # #构建应用表单
    form = AddAppNodeForm()

    app_name = request.form.get("app_name")
    # app_id = request.form.get("app_id")
    form_sorce = models.App_nodes.query.filter_by(app_name=app_name)[0]
    print app_name
    print form_sorce.app_id
    print form_sorce.app_name

    #该应用所部署的节点
    items = models.App_nodes.query.with_entities(models.App_nodes.node_id,
                                                 models.App_nodes.node_ip,
                                                 models.App_servers.env,
                                                 models.App_servers.status). \
        filter(models.App_nodes.app_name == form_sorce.app_name,
               models.App_nodes.node_id == models.App_servers.id).order_by(models.App_nodes.node_ip).all()
    total = len(items)

    return render_template('tomcat/node_list.html', form=form, object_list=items, total=total, APP_ENV=g.config.get('APP_ENV'))





# 添加项目重启
@bp.route('/addrestart/', methods=['GET', 'POST'])
def addrestart():

    # print "kkkkkkkkkkkkkkkkkkkkkkk"
    #构建一个添加重启表单
    form = AddRestartForm()
    app_name = request.args.get('app_name')

    if request.method == "POST":
        print form.app_name.data
        print form.auditor.data
        print request.form.getlist("cb")

        #应用tomcat重启批次状态为审批中
        status = 0
        print status
        # return "ok"        #return之后就不会执行后面的代码了

        #应用tomcat重启批次前缀
        batch_no_prefix = "TC-"

        #生成batch_no,strip去掉首尾空格
        batch_no = batch_no_prefix + form.app_name.data.strip() + "-" + datetime.now().strftime(
            '%Y%m%d%H%M%S')
        print batch_no
        return "ok"

        #根据所选的app,从数据库中得到它所对应的business_id
        form_sorce = models.Apps.query.filter_by(app_name=app_name)[0]

        # 通过表单构建数据库插入记录
        record = models.App_tomcat_restart(batch_no=batch_no,
                                           app_id=form.app_name.data.split(',')[0],
                                           app_name=form.app_name.data.split(',')[1],
                                           subject=form.subject.data,
                                           launcher=g.user.account,
                                           auditor=form.auditor.data,
                                           create_time=datetime.now(),
                                           business_id=form_sorce.business_id
                                           )
        # 写入数据库
        if record.save():
            ##发送消息通知
            receiver_list = []
            receiver_list.append(record.auditor)
            mes = Mess(receiver_list=receiver_list, mes_content=record.batch_no + '待审批', ext_info=record.batch_no)
            mes.sendInstationMes()
            # 邮件通知
            # if record.message_type == 1 or record.message_type == 3:
            #     mes.sendEmail()
            mes.sendEmail()

            # 保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='reboot',
                                                result=batch_no)
            # 写入数据库
            user_ac_record.save()

        #重定向回应用页面
        return redirect(url_for('tomcat.restart'))


        node_list = request.form.getlist('cb')
        action = request.form.get('btn')
        app_id = request.form.get('app_id')

        # 调试输出
        print node_list
        print action

        app = models.Apps.query.filter_by(id=app_id).first_or_404()

        # 设置type值：部署(0)，移除(1)，重启(2),tomcat打包(3),app打包(4),app部署(5),app和tomcat同时部署(6)
        if action == 'deploy':
            type = 0

        elif action == 'reboot':
            type = 2

        elif action == 'remove':
            type = 1

        elif action == 'appdeploy':
            type = 5

        elif action == 'tomcat_app_deploy':
            type = 6

        node_ip = node_list[0]
        # 根据传入的node_ip去查找这台服务器属于哪个业务
        app_server_attrs = models.App_servers.query.filter_by(inner_ip=node_ip).first_or_404()

        # 获取redis相关信息
        redis_attrs = models.Business.query.filter_by(id=app_server_attrs.business_id).first()


        # 根据节点列表，提交任务
        for node in node_list:
            app_node = models.App_nodes.query.filter_by(app_id=app.id, node_ip=node).first_or_404()

            # 生成batch_no
            task_no = 'TC-' + app.app_name.strip() + '-' + app_node.node_ip.replace('.',
                                                                                    '-') + '-' + datetime.now().strftime(
                '%Y%m%d%H%M%S')

            # 删除应用部署节点
            if type == 1:
                del_source = models.App_nodes.query.filter_by(app_id=app.id, node_ip=app_node.node_ip).first_or_404()
                del_source.delete()

            # 通过表单构建节点部署记录表插入记录
            record = models.App_tomcat_his(task_no=task_no,
                                           app_id=app.id,
                                           app_name=app.app_name,
                                           create_time=datetime.now(),
                                           node_id=app_node.node_id,
                                           node_ip=app_node.node_ip,
                                           app_path=app.app_path,
                                           tomcat_path=app.tomcat_path,
                                           status=0,  # 状态为排队中
                                           port=app.port,
                                           type=type)
            # 写入数据库
            if record.save():
                # 如果写入成功，任务加入redis队列
                # 构建一个加入队列json数据
                task_dic = {
                    "task_no": record.task_no,
                    "app_name": record.app_name.strip(),
                    "app_path": record.app_path.strip(),
                    "tomcat_path": record.tomcat_path.strip(),
                    "tomcat_port": record.port,
                    "node_ip": record.node_ip.strip(),
                    "type": record.type,
                    "beta_server": redis_attrs.beta_ip,
                    # "beta_server": app.beta_server,
                    # "rsync_path_name": app.rsync_path_name
                    # "rsync_path_name": g.config.get('RSYNC_PATH_NAME')[app_attrs.rsync_path_name]
                    "rsync_path_name": "www"

                }
                task_json = json.dumps(task_dic, skipkeys=True)

                # #增加任务到Redis队列
                # q = RedisQueue(queue_name, host=g.config.get('REDIS_HOST'), port=g.config.get('REDIS_PORT'),
                #                db=g.config.get('REDIS_DB'))
                # q.put(task_json)

                # 增加任务到Redis队列
                q = RedisQueue(queue_name, host=redis_attrs.redis_ip, port=redis_attrs.redis_port, db=redis_attrs.redis_db)
                q.put(task_json)

                # 保存用户操作记录
                user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                    account=g.user.account,
                                                    ip=g.user_real_ip,
                                                    action='tomcat_task',
                                                    result=record.app_name + '-' + record.node_ip)
                # 写入数据库
                user_ac_record.save()

        return redirect(url_for('tomcat.his'))
    #get请求
    else:
        # return "ok"
        # 获得应用的所有属性
        form.app_name.choices = [(a.app_name, a.app_name) for a in \
                             models.Apps.query.with_entities(
                                 models.Apps.app_name).filter(
                                 models.Apps.status == 1,
                                 models.Apps.site == models.Site_roles.site_id,
                                 models.Site_roles.business_id == models.Apps.business_id,
                                 models.User_business.business_id == models.Site_roles.business_id,
                                 models.User_business.user_id == models.Site_roles.user_id,
                                 models.Site_roles.user_id == g.user.id,
                             ).order_by(models.Apps.app_name)]


        # # 获得应用的所有属性
        # form.app_name.choices = [(a.app_attrs, a.app_name) for a in \
        #                      models.Apps.query.with_entities(func.concat(models.Apps.id).label(
        #                              'app_attrs'),
        #                          models.Apps.app_name).filter(
        #                          models.Apps.status == 1,
        #                          models.Apps.site == models.Site_roles.site_id,
        #                          models.Site_roles.business_id == models.Apps.business_id,
        #                          models.User_business.business_id == models.Site_roles.business_id,
        #                          models.User_business.user_id == models.Site_roles.user_id,
        #                          models.Site_roles.user_id == g.user.id,
        #                      ).order_by(models.Apps.app_name)]



        #审批人
        form.auditor.choices = [(a.account, a.username) for a in \
                                models.Users_role.query.with_entities(models.Users_role.account,
                                                                      models.Users_role.username).filter(
                                    models.Users_role.role_id == 3).order_by(models.Users_role.account).all()]

        #该应用所部署的节点
        items = models.App_nodes.query.with_entities(models.App_nodes.node_id,
                                                     models.App_nodes.node_ip,
                                                     models.App_servers.env.label('env_id'),
                                                     models.App_servers.env,
                                                     models.App_servers.status). \
            filter(models.App_nodes.app_name == app_name).order_by(models.App_nodes.node_ip).all()
        total = len(items)

        return render_template('tomcat/add_restart_tomcat.html', form=form)

        node_id = request.args.get('node_id')
        # 根据传入的node_ip去查找这台服务器属于哪个业务
        app_server_attrs = models.App_servers.query.filter_by(id=node_id).first_or_404()

        # 获取redis相关信息
        redis_attrs = models.Business.query.filter_by(id=app_server_attrs.business_id).first()



        print app_server_attrs.business_id
        print redis_attrs.id

        # 根据业务，使用不同的Redis队列
        if app_server_attrs.business_id == 1 and redis_attrs.id == 1:
            host = redis_attrs.redis_ip
            port = redis_attrs.redis_port
            db = redis_attrs.redis_db
            beta_server = redis_attrs.beta_ip
            # queue_name = 'Tomcat1'

        elif app_server_attrs.business_id == 2 and redis_attrs.id == 2:
            host = redis_attrs.redis_ip
            port = redis_attrs.redis_port
            db = redis_attrs.redis_db
            beta_server = redis_attrs.beta_ip
            # queue_name = 'Tomcat1'

        elif app_server_attrs.business_id == 3 and redis_attrs.id == 3:
            host = redis_attrs.redis_ip
            port = redis_attrs.redis_port
            db = redis_attrs.redis_db
            beta_server = redis_attrs.beta_ip
            # queue_name = 'Tomcat1'

        elif app_server_attrs.business_id == 4 and redis_attrs.id == 4:
            host = redis_attrs.redis_ip
            port = redis_attrs.redis_port
            db = redis_attrs.redis_db
            beta_server = redis_attrs.beta_ip
            # queue_name = 'Tomcat1'


        #通过GET方式是处理单条数据
        #接收2个参数，节点id和应用ID
        node_id = request.args.get('node_id')
        app_id = request.args.get('app_id')

        #type：部署(0)，移除(1)，重启(2),打包(3)
        type = request.args.get('type')

        app = models.Apps.query.filter_by(id=app_id).first_or_404()
        node = models.App_nodes.query.filter_by(app_id=app.id, node_id=node_id).first_or_404()

        #生成batch_no
        task_no = 'TC-' + app.app_name.strip() + '-' + node.node_ip.replace('.', '-') + '-' + datetime.now().strftime(
            '%Y%m%d%H%M%S')

        #通过表单构建节点部署记录表插入记录
        record = models.App_tomcat_his(task_no=task_no,
                                       app_id=app.id,
                                       app_name=app.app_name,
                                       create_time=datetime.now(),
                                       node_id=node.node_id,
                                       node_ip=node.node_ip,
                                       app_path=app.app_path,
                                       tomcat_path=app.tomcat_path,
                                       status=0,  #状态为排队中
                                       port=app.port,
                                       type=type)
        #写入数据库
        if record.save():
            #如果写入成功，任务加入redis队列
            #构建一个加入队列json数据
            task_dic = {
                "task_no": record.task_no,
                "app_name": record.app_name.strip(),
                "app_path": record.app_path.strip(),
                "tomcat_path": record.tomcat_path.strip(),
                "tomcat_port": record.port,
                "node_ip": record.node_ip.strip(),
                "type": record.type,
                # "beta_server": app.beta_server,
                "beta_server": redis_attrs.beta_ip,
                # "rsync_path_name": app.rsync_path_name
                "rsync_path_name": "www"
            }
            task_json = json.dumps(task_dic, skipkeys=True)

            # #增加任务到Redis队列
            # q = RedisQueue(queue_name, host=g.config.get('REDIS_HOST'), port=g.config.get('REDIS_PORT'),
            #                db=g.config.get('REDIS_DB'))
            # q.put(task_json)

            # 增加任务到Redis队列
            q = RedisQueue(queue_name, host=host, port=port, db=db)
            q.put(task_json)

            #保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='tomcat_task',
                                                result=record.app_name + '-' + record.node_ip)
            #写入数据库
            user_ac_record.save()

#审批重启通过
@bp.route('/approve_success/<batch_no>', methods=['GET', 'POST'])
@login_required
@AuditorPermission()
def approve_success(batch_no):
    object = models.App_tomcat_his.query.filter_by(batch_no=batch_no).first_or_404()
    #修改更新批次状态为2，待更新
    object.status = 2
    object.audit_time = datetime.now()
    if object.save():

        #保存用户操作记录
        user_ac_record = models.User_ac_log(uid=g.user.uid,
                                            account=g.user.account,
                                            ip=g.user_real_ip,
                                            action='approve_success',
                                            result=batch_no)
        #写入数据库
        user_ac_record.save()

        ##发送消息通知
        receiver_list = [(a.account) for a in models.Users_role.query.filter_by(role_id=4)]  #通知sa权限的成员
        receiver_list.append(object.launcher)

        mes = Mess(receiver_list=receiver_list, mes_content=object.batch_no + '审批通过', ext_info=object.batch_no)
        #站内消息通知
        mes.sendInstationMes()
        #邮件通知
        if object.message_type == 1 or object.message_type == 3:
            mes.sendEmail()

        #如果是自动更新，则进行更新操作
        if object.plan == 1:
            #整站更新直接操作
            if object.type == 0:
                return redirect(url_for('deploy.dodeploy', batch_no=batch_no))
            #增量更新要确保文件检查通过
            elif object.type == 1 and object.file_check == 1:
                return redirect(url_for('deploy.dodeploy', batch_no=batch_no))

    return redirect(url_for('deploy.deploygo', batch_no=batch_no))


