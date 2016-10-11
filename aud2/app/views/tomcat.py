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
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users, Site_roles, db
from ..forms import SearchAppForm, AddRestartForm, AddAppNodeForm, BatchForm
from ..utils.ldap_handle import openldap_conn_open, ad_conn_open
from ..utils.sms import gen_sms_vcode, send_sms, shadow_phone
from ..permissions import UserPermission, DeveloperPermission, AuditorPermission, SAPermission, AdminPermission



bp = Blueprint('tomcat', __name__)


#批量停止
@bp.route('/batch_restart/', methods = ['GET', 'POST'])
@login_required
@SAPermission()
def batch_restart():
    form = BatchForm()
    # form.node.choices = db.session.query(App_nodes.id, App_nodes.app_name).all()
    form.app.choices = db.session.query(Apps.id, Apps.app_name).all()
    if request.method == 'POST':
        print form.app.date
	return redirect(url_for('tomcat.his'))
    return render_template('tomcat/batch_resart_tomcat.html', form=form)


#批量停止应用
@bp.route('/batch_dostop/', methods = ['POST'])
@login_required
@SAPermission()
def batch_dostop():
    queue_name = 'Tomcat1'
    # print "gg" * 20
    app_id_list = [int(x) for x in request.form.getlist('app')] if request.form.getlist('app') != [''] else []
    # print app_id_list

    if not app_id_list or app_id_list == '':
        print "至少选择一个应用"

    # 应用tomcat重启批次前缀
    batch_no_prefix = "BATCH-TC"

    # 生成batch_no,strip去掉首尾空格
    batch_no = batch_no_prefix + "-" + datetime.now().strftime('%Y%m%d%H%M%S')

    # # 应用tomcat停止批次状态为审批中
    # status = 0

    # nodes_dict = {'app_name': node_list}
    nodes_dict = {}

    for item in app_id_list:
        # print "测试"
        # print item
        nodes = db.session.query(App_nodes.app_id, App_nodes.app_name, App_nodes.node_id, App_nodes.node_ip, App_nodes.business_id).filter(App_nodes.app_id == item).all()
        # print len(node)
        # print node[0]
        if not nodes:
            continue
        nodes_dict[nodes[0][0]] = []
        # print [(x[1], x[3]) for x in nodes]

        #将app_name的节点追加到这个字典中，实现{'aicai_webclient': ['192.168.91.40', '192.168.91.42']}
        #因为是根据id来走的，所以这里改成id {29L: [u'192.168.91.40', u'192.168.91.42']}
        map(lambda x: nodes_dict[nodes[0][0]].append(x), [ x[3] for x in nodes ])

    # print nodes_dict


    for key in nodes_dict:
        # print key, nodes_dict[key]

        #根据app_id来查询应用的属性值
        # app_attrs = models.Apps.query.filter_by(id=key).first_or_404()
        app_attrs1 = models.Apps.query.filter_by(id=key).all()
        #
        # for item in app_attrs1:
        #     print item.app_name

        for item in app_attrs1:

            print item.app_name, item.id
            # print "GG"*20
            #根据app_id获取应用的属性值
            app_attrs = models.Apps.query.filter_by(id=item.id).first_or_404()
            # print app_attrs.app_name

            #根据应用的bussiness_id获取redis相关信息
            redis_attrs = models.Business.query.filter_by(id=item.business_id).first_or_404()
            # print redis_attrs.beta_ip

            #根据app_id获取应用节点的信息
            app_nodes = models.App_nodes.query.filter_by(app_id=item.id).all()

            for node in app_nodes:
                print "GG" * 20
                print node.node_ip

                batch_no = batch_no
                #生成task_no
                task_no = 'TC-' + item.app_name.strip() + '-' + node.node_ip.replace('.',
                                                                                         '-') + '-' + datetime.now().strftime(
                '%Y%m%d%H%M%S')


                # 通过表单构建节点部署记录表插入记录
                record = models.App_tomcat_his(batch_no=batch_no,
                                               task_no=task_no,
                                               app_id=app_attrs.id,
                                               app_name=app_attrs.app_name,
                                               create_time=datetime.now(),
                                               node_id=node.node_id,
                                               node_ip=node.node_ip,
                                               app_path=app_attrs.app_path,
                                               tomcat_path=app_attrs.tomcat_path,
                                               status=0,  # 状态为排队中
                                               port=app_attrs.port,
                                               type = 7)
                #写入数据库
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

                    # 增加任务到Redis队列
                    q = RedisQueue(queue_name, host=redis_attrs.redis_ip, port=redis_attrs.redis_port,
                                   db=redis_attrs.redis_db)
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

#批量重启应用
@bp.route('/batch_dorestart/', methods = ['POST'])
@login_required
@SAPermission()
def batch_dorestart():
    queue_name = 'Tomcat1'
    # print "gg" * 20
    app_id_list = [int(x) for x in request.form.getlist('app')] if request.form.getlist('app') != [''] else []
    # print app_id_list

    if not app_id_list or app_id_list == '':
        print "至少选择一个应用"

    # 应用tomcat重启批次前缀
    batch_no_prefix = "BATCH-TC"

    # 生成batch_no,strip去掉首尾空格
    batch_no = batch_no_prefix + "-" + datetime.now().strftime('%Y%m%d%H%M%S')

    # # 应用tomcat停止批次状态为审批中
    # status = 0

    # nodes_dict = {'app_name': node_list}
    nodes_dict = {}

    for item in app_id_list:
        # print "测试"
        # print item
        nodes = db.session.query(App_nodes.app_id, App_nodes.app_name, App_nodes.node_id, App_nodes.node_ip, App_nodes.business_id).filter(App_nodes.app_id == item).all()
        # print len(node)
        # print node[0]
        if not nodes:
            continue
        nodes_dict[nodes[0][0]] = []
        # print [(x[1], x[3]) for x in nodes]

        #将app_name的节点追加到这个字典中，实现{'aicai_webclient': ['192.168.91.40', '192.168.91.42']}
        #因为是根据id来走的，所以这里改成id {29L: [u'192.168.91.40', u'192.168.91.42']}
        map(lambda x: nodes_dict[nodes[0][0]].append(x), [ x[3] for x in nodes ])

    # print nodes_dict


    for key in nodes_dict:
        # print key, nodes_dict[key]

        #根据app_id来查询应用的属性值
        # app_attrs = models.Apps.query.filter_by(id=key).first_or_404()
        app_attrs1 = models.Apps.query.filter_by(id=key).all()
        #
        # for item in app_attrs1:
        #     print item.app_name

        for item in app_attrs1:

            print item.app_name, item.id
            # print "GG"*20
            #根据app_id获取应用的属性值
            app_attrs = models.Apps.query.filter_by(id=item.id).first_or_404()
            # print app_attrs.app_name

            #根据应用的bussiness_id获取redis相关信息
            redis_attrs = models.Business.query.filter_by(id=item.business_id).first_or_404()
            # print redis_attrs.beta_ip

            #根据app_id获取应用节点的信息
            app_nodes = models.App_nodes.query.filter_by(app_id=item.id).all()

            for node in app_nodes:
                print "GG" * 20
                print node.node_ip

                batch_no = batch_no
                #生成task_no
                task_no = 'TC-' + item.app_name.strip() + '-' + node.node_ip.replace('.',
                                                                                         '-') + '-' + datetime.now().strftime(
                '%Y%m%d%H%M%S')


                # 通过表单构建节点部署记录表插入记录
                record = models.App_tomcat_his(batch_no=batch_no,
                                               task_no=task_no,
                                               app_id=app_attrs.id,
                                               app_name=app_attrs.app_name,
                                               create_time=datetime.now(),
                                               node_id=node.node_id,
                                               node_ip=node.node_ip,
                                               app_path=app_attrs.app_path,
                                               tomcat_path=app_attrs.tomcat_path,
                                               status=0,  # 状态为排队中
                                               port=app_attrs.port,
                                               type = 2)
                #写入数据库
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

                    # 增加任务到Redis队列
                    q = RedisQueue(queue_name, host=redis_attrs.redis_ip, port=redis_attrs.redis_port,
                                   db=redis_attrs.redis_db)
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

        elif action == 'stop':
            type = 7

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
# @SAPermission()
def restart(page=1):
    form = SearchAppForm()

    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        object_list = models.App_tomcat_restart.query.filter('app_name' + filter_string).order_by(
            desc(models.App_tomcat_restart.create_time)).limit(20).all()

        return render_template('tomcat/restart_tomcat.html', object_list=object_list, form=form,
                               TOMCAT_RESTART_STATUS=g.config.get('TOMCAT_RESTART_STATUS'))
    else:
        paginate = models.App_tomcat_restart.query.order_by(desc(models.App_tomcat_restart.create_time)).paginate(page,
                                                                                                          g.config.get(
                                                                                                              'POSTS_PER_PAGE'),
                                                                                                          False)
        object_list = paginate.items
        total = len(object_list)

        pagination = models.App_tomcat_restart.query.order_by(desc(models.App_tomcat_restart.create_time)).paginate(page,
                                                                                                            per_page=g.config.get(
                                                                                                                'POSTS_PER_PAGE'))

        return render_template('tomcat/restart_tomcat.html', object_list=object_list, form=form, pagination=pagination,
                               total=total,
                               TOMCAT_RESTART_STATUS=g.config.get('TOMCAT_RESTART_STATUS'))

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
    #构建一个添加重启表单
    form = AddRestartForm()
    if request.method == "POST":
        print form.subject.data
        print form.app_name.data
        print form.auditor.data
        print request.form.getlist("cb")

        app_name = form.app_name.data
        # app_name = request.args.get('app_name')
        print "post之前%s" % app_name

        # 根据所选的app,从数据库中得到它所对应的business_id
        form_sorce = models.Apps.query.filter_by(app_name=app_name)[0]
        #或
        # form_sorce = models.Apps.query.filter_by(app_name=app_name).first()
        app_id = form_sorce.id

        #复选框的IP列表
        node_list = request.form.getlist('cb')

        node_ip = node_list[0]
        # 根据传入的node_ip去查找这台服务器属于哪个业务
        app_server_attrs = models.App_servers.query.filter_by(inner_ip=node_ip).first_or_404()

        # 获取redis相关信息
        redis_attrs = models.Business.query.filter_by(id=app_server_attrs.business_id).first()

        #应用tomcat重启批次状态为审批中
        status = 0
        # return "ok"        #return之后就不会执行后面的代码了

        app = models.Apps.query.filter_by(app_name=app_name).first_or_404()

        # 应用tomcat重启批次前缀
        batch_no_prefix = "TC-"

        # 生成batch_no,strip去掉首尾空格
        batch_no = batch_no_prefix + app.app_name.strip() + "-" + datetime.now().strftime(
            '%Y%m%d%H%M%S')

        # 根据节点列表，提交任务
        for node in node_list:
            app_node = models.App_nodes.query.filter_by(app_id=app.id, node_ip=node).first_or_404()

            batch_no = batch_no

            # 生成task_no
            task_no = 'TC-' + app.app_name.strip() + '-' + app_node.node_ip.replace('.',
                                                                                    '-') + '-' + datetime.now().strftime(
                '%Y%m%d%H%M%S')

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
                                           type = 2)
            # 写入数据库
            if record.save():
                print "重启节点成功写入数据库"

        # 通过表单构建数据库插入记录
        record = models.App_tomcat_restart(batch_no=batch_no,
                                           app_id=form_sorce.id,
                                           app_name=form.app_name.data,
                                           status=status,
                                           launcher=g.user.account,
                                           auditor=form.auditor.data,
                                           create_time=datetime.now(),
                                           business_id=form_sorce.business_id,
                                           subject=form.subject.data)
        # 写入数据库
        if record.save():
            # print "OK"*20
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
                                                action='tomcat_reboot',
                                                result=batch_no)
            # 写入数据库
            user_ac_record.save()


        #重定向回应用页面
        return redirect(url_for('tomcat.restart'))
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

        # 该应用所部署节点，已经通过js在/node_list视图中做了
        # #该应用所部署的节点
        # items = models.App_nodes.query.with_entities(models.App_nodes.node_id,
        #                                              models.App_nodes.node_ip,
        #                                              models.App_servers.env.label('env_id'),
        #                                              models.App_servers.env,
        #                                              models.App_servers.status). \
        #     filter(models.App_nodes.app_name == app_name).order_by(models.App_nodes.node_ip).all()
        # total = len(items)

        return render_template('tomcat/add_restart_tomcat.html', form=form)


#审批重启通过
@bp.route('/approve_success/<batch_no>', methods=['GET', 'POST'])
@login_required
@AuditorPermission()
def approve_success(batch_no):
    object = models.App_tomcat_restart.query.filter_by(batch_no=batch_no).first_or_404()
    #修改重启批次状态为2，待重启
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

    return redirect(url_for('tomcat.restartgo', batch_no=batch_no))



#审批重启驳回
@bp.route('/approve_notgo/<batch_no>', methods=['GET', 'POST'])
@login_required
@AuditorPermission()
def approve_notgo(batch_no):
    object = models.App_tomcat_restart.query.filter_by(batch_no=batch_no).first_or_404()
    #修改更新批次状态为1，审核驳回
    object.status = 1
    object.audit_time = datetime.now()
    object.finish_time = datetime.now()

    if object.save():

        #保存用户操作记录
        user_ac_record = models.User_ac_log(uid=g.user.uid,
                                            account=g.user.account,
                                            ip=g.user_real_ip,
                                            action='approve_notgo',
                                            result=batch_no)
        #写入数据库
        user_ac_record.save()

        ##发送消息通知
        receiver_list = []
        receiver_list.append(object.launcher)
        receiver_list.append(object.auditor)
        mes = Mess(receiver_list=receiver_list, mes_content=object.batch_no + '审批未通过', ext_info=object.batch_no)
        mes.sendInstationMes()

        mes.sendEmail()

    return redirect(url_for('tomcat.restartgo', batch_no=batch_no))


#不更新
@bp.route('/notgo/<batch_no>', methods=['GET', 'POST'])
@login_required
def notgo(batch_no):
    object = models.App_tomcat_restart.query.filter_by(batch_no=batch_no).first_or_404()

    #增加权限判断，发起人、审批人和sa/admin权限可更新
    if SAPermission().check() or object.launcher == g.user.account or object.auditor == g.user.account:
        pass
    else:
        abort(403)

    #修改更新批次状态为6，取消更新
    object.status = 6
    object.finish_time = datetime.now()

    if object.save():

        #保存用户操作记录
        user_ac_record = models.User_ac_log(uid=g.user.uid,
                                            account=g.user.account,
                                            ip=g.user_real_ip,
                                            action='notgo',
                                            result=batch_no)
        #写入数据库
        user_ac_record.save()

        ##发送消息通知
        receiver_list = []
        receiver_list.append(object.launcher)
        mes = Mess(receiver_list=receiver_list, mes_content=object.batch_no + '取消更新', ext_info=object.batch_no)
        mes.sendInstationMes()
        #邮件通知
        mes.sendEmail()

    return redirect(url_for('tomcat.restartgo', batch_no=batch_no))

#更新进度查询
@bp.route('/restartgo/<batch_no>', methods=['GET', 'POST'])
@login_required
def restartgo(batch_no):
    batch = models.App_tomcat_restart.query.with_entities(models.App_tomcat_restart.batch_no,
                                                        models.App_tomcat_restart.id,
                                                        models.App_tomcat_restart.subject,
                                                        models.App_tomcat_restart.app_id,
                                                        models.App_tomcat_restart.app_name,
                                                        models.App_tomcat_restart.status,
                                                        models.App_tomcat_restart.auditor,
                                                        models.App_tomcat_restart.operator,
                                                        models.App_tomcat_restart.business_id,
                                                        models.App_tomcat_restart.launcher,
                                                        models.Users.username).filter(
        models.App_tomcat_restart.batch_no == batch_no,
        models.App_tomcat_restart.launcher == models.Users.account).first_or_404()

    # #数据库查询对象转换为字典
    object = batch._asdict()
    #
    # #替换文本中的换行符
    # if object.get('content'):
    #     object['content'] = object.get('content').replace('\r\n', '<br/>')
    # if object.get('desc'):
    #     object['desc'] = object.get('desc').replace('\r\n', '<br/>')

    #部署服务器列表
    node_list = models.App_tomcat_his.query.filter_by(batch_no=batch_no).all()
    # print node_list.node_ip

    #备注
    remark_list = models.Deploy_batch_remarks.query.with_entities(models.Users.username,
                                                                  models.Deploy_batch_remarks.create_time,
                                                                  models.Deploy_batch_remarks.content).filter(
        models.Deploy_batch_remarks.batch_id == object['id'],
        models.Deploy_batch_remarks.uid == models.Users.uid).order_by(models.Deploy_batch_remarks.create_time).all()
    #和该批次有关的行为
    ac_list = models.User_ac_log.query.with_entities(models.Users.username,
                                                     models.User_ac_log.create_time,
                                                     models.User_ac_log.action).filter(
        models.User_ac_log.result == batch_no,
        models.User_ac_log.account == models.Users.account).order_by(models.User_ac_log.create_time).all()

    #获取审批权限和SA权限以上的人员名单
    manager_list = [(a.account, a.username) for a in models.Users_role.query.with_entities(models.Users.username,
                                                                                           models.Users.account).filter(
        or_(and_(models.Users_role.uid == models.Users.uid, models.Users_role.role_id >= 3),
            models.Users.account == batch.operator))]
    manager_dict = dict(manager_list)



    return render_template('tomcat/restartgo.html',
                           object=object,
                           node_list=node_list,
                           remark_list=remark_list,
                           BUSSINESS_TYPE=g.config.get('BUSSINESS_TYPE'),
                           RESTART_NODETASK_STATUS=g.config.get('RESTART_NODETASK_STATUS'),
                           TOMCAT_RESTART_STATUS=g.config.get('TOMCAT_RESTART_STATUS'),
                           ac_list=ac_list,
                           USER_ACTION_CONVERT=g.config.get('USER_ACTION_CONVERT'),
                           manager_dict=manager_dict)



# #审批重启通过
# @bp.route('/approve_success/<batch_no>', methods=['GET', 'POST'])
# @login_required
# @AuditorPermission()
# def approve_success(batch_no):
#     object = models.App_tomcat_restart.query.filter_by(batch_no=batch_no).first_or_404()
#     #修改重启批次状态为2，待重启
#     object.status = 2
#     object.audit_time = datetime.now()
#     if object.save():
#
#         #保存用户操作记录
#         user_ac_record = models.User_ac_log(uid=g.user.uid,
#                                             account=g.user.account,
#                                             ip=g.user_real_ip,
#                                             action='approve_success',
#                                             result=batch_no)
#         #写入数据库
#         user_ac_record.save()
#
#     return redirect(url_for('tomcat.restartgo', batch_no=batch_no))


#执行重启
@bp.route('/dorestart/<batch_no>', methods=['GET', 'POST'])
@login_required
def dorestart(batch_no):
    queue_name = 'Tomcat1'
    print queue_name

    restart_batch = models.App_tomcat_restart.query.filter_by(batch_no=batch_no).first_or_404()
    # 修改重启批次状态为3，重启中
    restart_batch.status = 3
    restart_batch.audit_time = datetime.now()

    if restart_batch.save():
    #保存用户操作记录
        user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='do_tomcat_restart',
                                                result=batch_no)
    #写入数据库
        user_ac_record.save()

    # if request.method == "POST":
    # restart_batch = models.app_tomcat_restart.query.filter_by(batch_no=batch_no).first_or_404()
    # 根据传入的batch_no去查找对应节点的任务
    restart_attrs1 = models.App_tomcat_his.query.filter_by(batch_no=batch_no).all()
    # print  len(restart_attrs1)
    # print type(restart_attrs1)


    restart_attrs = models.App_tomcat_his.query.filter_by(batch_no=batch_no).first_or_404()

    #根据batch_no查找出对应app的信息
    app_attrs = models.Apps.query.filter_by(app_name=restart_attrs.app_name).first_or_404()

    # 获取redis相关信息
    redis_attrs = models.Business.query.filter_by(id=app_attrs.business_id).first()

    # print restart_attrs.node_ip
    # print redis_attrs.beta_ip
    #定义一个字典存放node_ip 和 task_no 的值
    node_dict = {}
    for i in restart_attrs1:
        # print i.node_ip
        # print i.task_no
        node_dict[i.node_ip] = i.task_no


    # 根据节点列表，提交任务
    for (node_ip, task_no) in node_dict.items():
        task_dic = {
            "batch_no": batch_no,
            "task_no": str(task_no),
            "app_name": restart_attrs.app_name.strip(),
            "app_path": restart_attrs.app_path.strip(),
            "tomcat_path": restart_attrs.tomcat_path.strip(),
            "tomcat_port": restart_attrs.port,
            # "node_ip": restart_attrs.node_ip.strip(),
            "node_ip": node_ip,
            "type": restart_attrs.type,
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
        # user_ac_record = models.User_ac_log(uid=g.user.uid,
        #                                     account=g.user.account,
        #                                     ip=g.user_real_ip,
        #                                     action='tomcat_task'
        #                                     # result=record.app_name + '-' + record.node_ip)
        # # 写入数据库
        # user_ac_record.save()

    return redirect(url_for('tomcat.restartgo', batch_no=batch_no))
    # return redirect(url_for('tomcat.his'))
