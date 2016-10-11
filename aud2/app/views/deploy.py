# coding: utf-8
__author__ = 'lancger'

from flask import render_template, request, redirect, url_for, Blueprint, flash, g, \
    session, current_app
from .. import models, db
from flask.ext.login import login_user, logout_user, login_required
from datetime import datetime, date, timedelta
from ..forms import LoginForm, SearchSiteForm, SearchServerForm, SearchAppForm, AddDeployForm, EditDeployForm, AddRestartForm
#from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_action_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users
from sqlalchemy import desc, func, or_, and_
from ..permissions import UserPermission, DeveloperPermission, AuditorPermission, SAPermission, AdminPermission
# from app import app
import os
import shutil
import hashlib, json
from ..utils.redisqueue import RedisQueue
from ..utils.message import Mess
from ..utils.ldap_handle import openldap_conn_open
from ..utils.ldap_sync_user import ldapConnOpen, ldapHandle
# from ..permissions import SSPermission

bp = Blueprint('deploy', __name__)

#列出服务器(普通用户权限)
@bp.route('/query', methods=['GET', 'POST'])
@bp.route('/query/<int:page>', methods=['GET', 'POST'])
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
                                                                                models.Apps.business_id,
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

        return render_template('servers/l_apps.html', total=total, object_list=object_list, form=form)
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
                                                                                models.Apps.business_id,
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

        return render_template('deploy/l_apps.html', total=total, object_list=object_list, form=form,
                               tomcat_count=tomcat_count)


#列出最近20条更新任务
@bp.route('/list', methods=['GET', 'POST'])
@login_required
def deploy():
    form = SearchSiteForm()

    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'

        object_list = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.batch_no,
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
                                                                  models.App_deploy_batch.launcher,
                                                                  models.Users.username).filter(
            models.App_deploy_batch.launcher == models.Users.account, 'app_name' + filter_string).order_by(
            desc(models.App_deploy_batch.create_time)).limit(20).all()

        #object_list = models.App_deploy_batch.query.filter('app_name' + filter_string).order_by(desc(models.App_deploy_batch.create_time)).limit(20).all()

        return render_template('deploy/deploy.html', object_list=object_list, form=form, APP_ENV=g.config.get('APP_ENV'),
                               DEPLOY_STATUS=g.config.get('DEPLOY_STATUS'), DEPLOY_TYPE=g.config.get('DEPLOY_TYPE'))
    else:
        print g.user.id
        
        object_list = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.batch_no,
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
                                                                  models.App_deploy_batch.launcher,
                                                                  models.App_deploy_batch.business_id,
                                                                  models.User_business.business_id,
                                                                  models.Users.username).filter(
            models.App_deploy_batch.launcher == models.Users.account,
            models.User_business.user_id == g.user.id,
            models.User_business.business_id == models.App_deploy_batch.business_id
            #models.App_deploy_batch.business_id == models.User_business.business_id
        ).order_by(
            desc(models.App_deploy_batch.create_time)).limit(20).all()


        # #获得应用的所有属性
        # form.app_name.choices = [(a.app_attrs, a.app_name) for a in \
        #                          models.Apps.query.with_entities(func.concat(models.Apps.id, ",",
        #                                                                      models.Apps.app_name, ",",
        #                                                                      models.Apps.app_path, ",",
        #                                                                      models.Apps.tomcat_path, ",",
        #                                                                      models.Apps.port, ",",
        #                                                                      models.Apps.shutdown_port).label(
        #                              'app_attrs'),
        #                                                          models.Apps.app_name).filter(
        #                                                                      models.Apps.status == 1,
        #                                                                      models.Apps.site == models.Site_roles.site_id,
        #                                                                      models.Site_roles.business_id == models.Apps.business_id,
        #                                                                      models.User_business.business_id == models.Site_roles.business_id,
        #                                                                      models.User_business.user_id == models.Site_roles.user_id,
        #                                                                      models.Site_roles.user_id == g.user.id,
        #                                                                      ).order_by(models.Apps.app_name)]

        return render_template('deploy/deploy.html', object_list=object_list, form=form, APP_ENV=g.config.get('APP_ENV'),
                               DEPLOY_STATUS=g.config.get('DEPLOY_STATUS'), DEPLOY_TYPE=g.config.get('DEPLOY_TYPE'))


#编辑更新
@bp.route('/editdeploy/<batch_id>', methods=['GET', 'POST'])
@login_required
def editdeploy(batch_id):
    object = models.App_deploy_batch.query.filter_by(id=batch_id).first_or_404()

    #增加权限判断，发起人、审批人和sa/admin权限可更新
    if SAPermission().check() or object.launcher == g.user.account or object.auditor == g.user.account:
        pass
    else:
        abort(403)

    #构建一个表单
    form = EditDeployForm()

    #POST请求
    if request.method == "POST":
        #增量更新要检查更新文件是否有提交
        if form.type.data == 1:
            if not form.content.data:
                flash("增量更新必须提交更新文件!")
                return redirect(url_for('editdeploy', batch_id=batch_id))
            else:
                #将更新内容写入文件
                file_list = os.path.join(g.config.get('UPDATE_FILE_LIST'), object.batch_no)
                file_list_url = ''
                if len(form.content.data):
                    file_list_url = 'http://aud2.inzwc.com/filelist/' + object.batch_no
                    with open(file_list, 'w') as file:
                        file.write(form.content.data)

                object.content = file_list_url
                print "更新失败排查"
                print file_list_url
                print object.content
                print "更新失败排查"
                object.file_check = 0

        message_cc = ''
        if form.message_cc.data:
            message_cc = ','.join(form.message_cc.data)

        object.subject = form.subject.data
        object.plan = form.plan.data
        object.type = form.type.data
        object.auditor = form.auditor.data
        object.message_type = form.message_type.data
        object.restart_tomcat = form.restart_tomcat.data
        object.message_cc = message_cc
        object.before_command = form.before_command.data
        object.after_command = form.after_command.data
        object.desc = form.desc.data
        object.create_time = datetime.now()

        #写入数据库
        if object.save():
            #保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='editdeploy',
                                                result=object.batch_no)
            #写入数据库
            user_ac_record.save()

        #重定向回应用页面
        return redirect(url_for('deploy.deploy'))

    else:

        form.batch_no.data = object.batch_no
        form.app_name.data = object.app_name
        form.subject.data = object.subject
        form.plan.data = object.plan
        form.type.data = object.type
        form.batch_no.data = object.batch_no
        form.env.data = object.env
        form.auditor.data = object.auditor
        form.message_type.data = object.message_type
        form.restart_tomcat.data = object.restart_tomcat
        form.message_cc.data = object.message_cc
        form.before_command.data = object.before_command
        form.after_command.data = object.after_command
        form.desc.data = object.desc

        #部分更新需要从文件读取内容填充
        if form.type.data == 1:
            file_list = os.path.join(g.config.get('UPDATE_FILE_LIST'), object.batch_no)
            with open(file_list) as file:
                form.content.data = file.read()


        #更新安排
        form.plan.choices = [(item, g.config.get('DEPLOY_PLAN')[item]) for item in
                             range(len(g.config.get('DEPLOY_PLAN')))]

        #数据库中选择业务类别
        form.business_id.choices = [(a.id, a.business_name) for a in \
                                    models.Business.query.order_by(models.Business.business_name).all()]

        #更新方式
        form.type.choices = [(item, g.config.get('ADD_DEPLOY_TYPE')[item]) for item in
                             range(len(g.config.get('ADD_DEPLOY_TYPE')))]
        #通知方式
        form.message_type.choices = [(item, g.config.get('MESSAGE_TYPE')[item]) for item in
                                     range(len(g.config.get('MESSAGE_TYPE')))]

        #通知抄送
        form.message_cc.choices = [(a.account, a.username) for a in \
                                   models.Users.query.order_by(models.Users.username).all()]

        #环境：0 测试环境，1 beta环境，2 生产环境
        form.env.choices = [(item, g.config.get('APP_ENV')[item]) for item in range(len(g.config.get('APP_ENV')))]
        #审批人
        form.auditor.choices = [(a.account, a.username) for a in \
                                models.Users_role.query.with_entities(models.Users_role.account,
                                                                      models.Users_role.username).filter(
                                    models.Users_role.role_id == 3).order_by(models.Users_role.account).all()]

        return render_template('deploy/editdeploy.html', form=form)


#创建一个更新流程
'''
流程：
1.发起更新：更新配置存入更新批次表App_deploy_batch，状态审批中/更新中。
2.更新任务拆分：根据应用节点部署情况，拆分对应数量的更新任务，提交到Redis队列，如成功则存入更新历史表，状态为排队中
3.Client端从Redis获取任务，获取任务成功，通过json接口修改更新历史表对应记录状态为更新中，同时删除任务，并在client执行
4.执行完成后提交结果，通过json接口修改对应记录状态为成功或失败，并提交成功或失败日志到更新情况记录表(记录日志)。
5.当所有更新任务完成后，个性更新批次表状态为成功或异常，只要有一个更新失败，状态就为异常。同时发送更新结果消息如邮件或短信。

更新批次表状态转变：审批中(测试和beta无需审批)＝》更新中＝》成功/异常
更新历史表状态转变：排队中＝》更新中＝》成功/失败

先不做审批，更新核心功能完成后再做。
更新批次号：
T/B/PU-应用名-20150716213101，如PU-aicai_webclient-20150716213101
回滚批次号：
如PR-aicai_webclient-20150716213101

任务号：
批次号+ip做hash或md5
'''


@bp.route('/adddeploy', methods=['GET', 'POST'])
@login_required
def adddeploy():
    #构建一个添加应用表单
    form = AddDeployForm()
    #获取redis相关信息
    # redis_attrs = models.Business.query.filter_by(id=deploy_batch.business_id).first()

    #POST请求
    if request.method == "POST":
        # print "&&"*20
        # print form.business_id.data
        # print "%%%"*20
        #增量更新要检查更新文件是否有提交
        if form.type.data == 1:
            if not form.content.data:
                flash("增量更新必须提交更新文件!")
                return redirect(url_for('deploy.adddeploy'))

        #增加更新业务和业务的校验功能
        business_num = models.Apps.query.filter_by(app_name=form.app_name.data.split(',',2)[1]).first()
        print "-------------"
        print form.business_id.data
        #print form.app_name.data.split(',',2)
        print form.app_name.data.split(',',2)[1]
        print business_num.business_id
        print "-------------"

        if form.business_id.data != business_num.business_id:
            flash("项目名称跟业务类型不对称!")
            return redirect(url_for('deploy.adddeploy'))

        ###生成更新批次号前缀，开始===
        #daily测试环境更新
        if form.env.data == 0:
            #整站更新
            if form.type.data == 0:
                batch_no_prefix = "UDA-"
            #更新批次状态为更新中，不须审批
            status = 1
            #根据环境，使用不同的Redis队列
            queue_name = 'daily'
        #project测试环境更新
        elif form.env.data == 1:
            #整站更新
            if form.type.data == 0:
                batch_no_prefix = "UPA-"
            #更新批次状态为更新中，不须审批
            status = 1
            #根据环境，使用不同的Redis队列
            queue_name = 'project'
        #beta环境更新
        elif form.env.data == 2:
            #整站更新
            if form.type.data == 0:
                batch_no_prefix = "UBA-"
            #更新批次状态为更新中，不须审批
            status = 1
            #根据环境，使用不同的Redis队列
            queue_name = 'beta'
        #生产环境更新
        elif form.env.data == 3:
            # print "%00%"*20
            # print form.business_id.data
            # # print "%0%%"*20
            #整站更新
            if form.type.data == 0:
                batch_no_prefix = "UOA-"
                queue_name = 'production1'
                #根据环境，使用不同的Redis队列
                #爱彩业务redis信息 business_id 为1 192.168.91.41  production1
                #if form.business_id == 1:
                #    print "%00%"*20
                #    # print form.business_id.data
                #    # print "%00%%"*20
                #    queue_name = 'production1'
                ##滴滴业务redis信息，business_id 为2 192.168.91.230  production1
                #elif form.business_id == 2:
                #    queue_name = 'production1'
                ##配资业务redis信息，business_id 为3 192.168.91.232  production1
                #elif form.business_id == 3:
                #    queue_name = 'production1'
                ##金融业务redis信息，business_id 为4 192.168.91.234  production1
                #elif form.business_id == 4:
                #    queue_name = 'production1'
            #增量更新
            elif form.type.data == 1:
                batch_no_prefix = "UOI-"
                queue_name = 'production1'
                #根据环境，使用不同的Redis队列
                #if form.business_id == 1:
                #    queue_name = 'production1'
                #elif form.business_id == 2:
                #    queue_name = 'production1'
                #elif form.business_id == 3:
                #    queue_name = 'production1'
                #elif form.business_id == 4:
                #    queue_name = 'production1'
            #更新批次状态为审批中
            status = 0
            #根据环境，使用不同的Redis队列
            # queue_name = 'production'
        ###生成更新批次号前缀，结束===

        #生成batch_no,strip去掉首尾空格
        batch_no = batch_no_prefix + form.app_name.data.split(',')[1].strip() + "-" + datetime.now().strftime(
            '%Y%m%d%H%M%S')

        #将更新内容写入文件
        file_list = os.path.join(g.config.get('UPDATE_FILE_LIST'), batch_no)
        file_list_url = ''
        if len(form.content.data):
            file_list_url = 'http://aud2.inzwc.com/filelist/' + batch_no
            with open(file_list, 'w') as file:
                file.write(form.content.data)

        message_cc = ''
        if form.message_cc.data:
            message_cc = ','.join(form.message_cc.data)


        #通过表单构建数据库插入记录
        record = models.App_deploy_batch(batch_no=batch_no,
                                         app_id=form.app_name.data.split(',')[0],
                                         app_name=form.app_name.data.split(',')[1],
                                         subject=form.subject.data,
                                         plan=form.plan.data,
                                         type=form.type.data,
                                         status=status,
                                         env=form.env.data,
                                         launcher=g.user.account,
                                         # launcher='manbo.xu',
                                         auditor=form.auditor.data,
                                         message_type=form.message_type.data,
                                         restart_tomcat=form.restart_tomcat.data,
                                         message_cc=message_cc,
                                         before_command=form.before_command.data,
                                         after_command=form.after_command.data,
                                         desc=form.desc.data,
                                         content=file_list_url,
                                         create_time=datetime.now(),
                                         business_id=form.business_id.data)
        #写入数据库
        if record.save():
            ##发送消息通知
            receiver_list = []
            receiver_list.append(record.auditor)
            mes = Mess(receiver_list=receiver_list, mes_content=record.batch_no + '待审批', ext_info=record.batch_no)
            mes.sendInstationMes()
            #邮件通知
            if record.message_type == 1 or record.message_type == 3:
                mes.sendEmail()

            #保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='adddeploy',
                                                result=batch_no)
            #写入数据库
            user_ac_record.save()

        #重定向回应用页面
        return redirect(url_for('deploy.deploy'))

    #GET请求
    else:
        #获得应用的所有属性
        #print models.Users.query.filter(models.Users.id==g.user.id).first()
        print db.session.query(models.Users.id,models.Users.username).filter(models.Users.id==g.user.id).first()[1]
        print "用户ID%s"%g.user.id
        print g.user.username
        form.app_name.choices = [(a.app_attrs, a.app_name) for a in \
                                 models.Apps.query.with_entities(func.concat(models.Apps.id, ",",
                                                                             models.Apps.app_name, ",",
                                                                             models.Apps.app_path, ",",
                                                                             models.Apps.tomcat_path, ",",
                                                                             models.Apps.port, ",",
                                                                             models.Apps.shutdown_port).label(
                                     'app_attrs'),
                                                                 models.Apps.app_name).filter(
                                                                             models.Apps.status == 1,
                                                                             models.Apps.site == models.Site_roles.site_id,
                                                                             models.Site_roles.business_id == models.Apps.business_id,
                                                                             models.User_business.business_id == models.Site_roles.business_id,
                                                                             models.User_business.user_id == models.Site_roles.user_id,
                                                                             models.Site_roles.user_id == g.user.id,
                                                                             ).order_by(models.Apps.app_name)]
        #更新安排
        form.plan.choices = [(item, g.config.get('DEPLOY_PLAN')[item]) for item in
                             range(len(g.config.get('DEPLOY_PLAN')))]

        #更新方式
        form.type.choices = [(item, g.config.get('ADD_DEPLOY_TYPE')[item]) for item in
                             range(len(g.config.get('ADD_DEPLOY_TYPE')))]
        #通知方式
        form.message_type.choices = [(item, g.config.get('MESSAGE_TYPE')[item]) for item in
                                     range(len(g.config.get('MESSAGE_TYPE')))]

        #通知抄送
        form.message_cc.choices = [(a.account, a.username) for a in \
                                   models.Users.query.order_by(models.Users.username).all()]

        # #业务选择，(0 彩票业务, 1 金融业务 , 2 滴滴业务， 3 配资业务， 4 新增业务)
        # form.business_id.choices = [(item, g.config.get('BUSSINESS_TYPE')[item]) for item in range(len(g.config.get('BUSSINESS_TYPE')))]

        #数据库中选择业务类别
        #form.business_id.choices = [(a.id, a.business_name) for a in \
        #                            models.Business.query.order_by(models.Business.business_name).all()]
        
        #数据库中根据分配权限过滤业务类别
        form.business_id.choices = [(a.id, a.business_name) for a in \
                         models.Business.query.filter(
                         models.Business.id==models.User_business.business_id,
                         models.User_business.user_id==g.user.id,
                     ).order_by(models.Business.business_name)]      

        #环境：0 测试环境，1 beta环境，2 生产环境
        form.env.choices = [(item, g.config.get('APP_ENV')[item]) for item in range(len(g.config.get('APP_ENV')))]
        #审批人
        form.auditor.choices = [(a.account, a.username) for a in \
                                models.Users_role.query.with_entities(models.Users_role.account,
                                                                      models.Users_role.username).filter(
                                    models.Users_role.role_id == 3).order_by(models.Users_role.account).all()]

        return render_template('deploy/adddeploy.html', form=form)


#审批更新通过
@bp.route('/approve_success/<batch_no>', methods=['GET', 'POST'])
@login_required
@AuditorPermission()
def approve_success(batch_no):
    object = models.App_deploy_batch.query.filter_by(batch_no=batch_no).first_or_404()
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


#审批更新驳回
@bp.route('/approve_notgo/<batch_no>', methods=['GET', 'POST'])
@login_required
@AuditorPermission()
def approve_notgo(batch_no):
    object = models.App_deploy_batch.query.filter_by(batch_no=batch_no).first_or_404()
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
        #邮件通知
        if object.message_type == 1 or object.message_type == 3:
            mes.sendEmail()

    return redirect(url_for('deploy.deploygo', batch_no=batch_no))


#不更新
@bp.route('/notgo/<batch_no>', methods=['GET', 'POST'])
@login_required
def notgo(batch_no):
    object = models.App_deploy_batch.query.filter_by(batch_no=batch_no).first_or_404()

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
        if object.message_type == 1 or object.message_type == 3:
            mes.sendEmail()

    return redirect(url_for('deploy.deploygo', batch_no=batch_no))


#执行更新
@bp.route('/dodeploy/<batch_no>', methods=['GET', 'POST'])
@login_required
def dodeploy(batch_no):
    queue_name = 'production1'

    deploy_batch = models.App_deploy_batch.query.filter_by(batch_no=batch_no).first_or_404()

    #获取redis相关信息
    # redis_attrs = models.Business.query.filter_by(id=deploy_batch.business_id).first()

    redis_attrs = models.Business.query.filter_by(id=deploy_batch.business_id).first()


    #如果更新批次状态为更新中,则直接跳转，避免重复更新操作
    if deploy_batch.status >= 3:
        return redirect(url_for('deploy.deploygo', batch_no=batch_no))

    #增量更新文件检查必须通过
    if deploy_batch.type == 1 and deploy_batch.file_check == 0:
        flash("增量更新请确保更新文件检查通过!")
        return redirect(url_for('deploy.deploygo', batch_no=batch_no))  # 根据环境，使用不同的Redis队列

    if deploy_batch.business_id == 1 and redis_attrs.id == 1:
        host = redis_attrs.redis_ip
        port = redis_attrs.redis_port
        db = redis_attrs.redis_db
        beta_server = redis_attrs.beta_ip

    elif deploy_batch.business_id == 2 and redis_attrs.id == 2:
        host = redis_attrs.redis_ip
        port = redis_attrs.redis_port
        db = redis_attrs.redis_db
        beta_server = redis_attrs.beta_ip

    elif deploy_batch.business_id == 3 and redis_attrs.id == 3:
        host = redis_attrs.redis_ip
        port = redis_attrs.redis_port
        db = redis_attrs.redis_db
        beta_server = redis_attrs.beta_ip

    elif deploy_batch.business_id == 4 and redis_attrs.id == 4:
        host = redis_attrs.redis_ip
        port = redis_attrs.redis_port
        db = redis_attrs.redis_db
        beta_server = redis_attrs.beta_ip

    elif deploy_batch.business_id == 5 and redis_attrs.id == 5:
        host = redis_attrs.redis_ip
        port = redis_attrs.redis_port
        db = redis_attrs.redis_db
        beta_server = redis_attrs.beta_ip

    #任务拆分
    nodes = models.App_nodes.query.with_entities(models.App_nodes.id, models.App_nodes.node_ip). \
        filter(models.App_nodes.node_id == models.App_servers.id,
               models.App_nodes.app_id == deploy_batch.app_id,
               models.App_servers.env == deploy_batch.env).all()

    #获取应用属性
    app_attrs = models.Apps.query.filter_by(id=deploy_batch.app_id).first()

    j = 0
    nodes_count = len(nodes)

    for node in nodes:

        j = j + 1

        #如果需要重启tomcat或全站更新
        if int(deploy_batch.restart_tomcat) == 1 or int(deploy_batch.type) == 0:
            #如果节点数量超过2，则将节点分成2部分，第2部分延迟更新30秒
            if int(nodes_count / 2) == 0 or j <= int(nodes_count / 2):
                task_delay_time = 0
            else:
                task_delay_time = 30
        else:
            task_delay_time = 0

        #生成任务号task_no：md5(batch_no+节点IP+当前时间)
        task_no = hashlib.new("md5", batch_no + node.node_ip + str(datetime.now())).hexdigest()

        #创建节点任务插入记录
        task_record = models.App_deploy_node_task(task_no=task_no,
                                                  batch_id=deploy_batch.id,
                                                  batch_no=batch_no,
                                                  node_id=node.id,
                                                  node_ip=node.node_ip,
                                                  status=0,
                                                  create_time=datetime.now())
        #写入数据库
        if task_record.save():
            #如果写入成功，任务加入redis队列
            #构建一个加入队列json数据
            task_dic = {
                "task_no": task_no,
                "app_name": app_attrs.app_name.strip(),
                "app_path": app_attrs.app_path.strip(),
                "tomcat_path": app_attrs.tomcat_path.strip(),
                "tomcat_port": app_attrs.port,
                "shutdown_port": app_attrs.shutdown_port,
                "batch_no": deploy_batch.batch_no,
                "type": deploy_batch.type,
                "restart_tomcat": deploy_batch.restart_tomcat,
                "before_command": deploy_batch.before_command,
                "after_command": deploy_batch.after_command,
                "file_list_url": deploy_batch.content,
                "node_ip": task_record.node_ip.strip(),
                # "rsync_path_name": app_attrs.rsync_path_name,
                "rsync_path_name": g.config.get('RSYNC_PATH_NAME')[app_attrs.rsync_path_name],
                "delay_time": task_delay_time,
                # "beta_server": app_attrs.beta_server,
                "beta_server": redis_attrs.beta_ip,
                # "business_id": deploy_batch.business_id,
                "business_id": redis_attrs.id
            }
            task_json = json.dumps(task_dic, skipkeys=True)


            #增加任务到Redis队列
            q = RedisQueue(queue_name, host=host, port=port, db=db)
            q.put(task_json)

            # #增加任务到Redis队列
            # q = RedisQueue(queue_name, host=g.config.get('REDIS_HOST'), port=g.config.get('REDIS_PORT'),
            #                db=g.config.get('REDIS_DB'))
            # q.put(task_json)


    print "MMM"*20
    print g.config.get('RSYNC_PATH_NAME')[app_attrs.rsync_path_name]
    print "MMM"*20
    #修改更新批次状态为更新中
    deploy_batch.status = 3
    # deploy_batch.operator = g.user.account

    if deploy_batch.save():
        # flash("更新中")
        # 保存用户操作记录
        user_ac_record = models.User_ac_log(uid=g.user.uid,
                                            account=g.user.account,
                                            ip=g.user_real_ip,
                                            action='dodeploy',
                                            result=batch_no)
        #写入数据库
        user_ac_record.save()

    return redirect(url_for('deploy.deploygo', batch_no=batch_no))

#回滚
@bp.route('/rollback/<batch_no>', methods=['GET', 'POST'])
@login_required
@SAPermission()
def rollback(batch_no):
    deploy_batch = models.App_deploy_batch.query.filter_by(batch_no=batch_no).first_or_404()

    # 获取redis相关信息
    redis_attrs = models.Business.query.filter_by(id=deploy_batch.business_id).first()

    #如果已经回滚过，则直接返回页面，不进行回滚操作，避免重复回滚
    if deploy_batch.is_undo == 1:
        #重定向回应用页面
        return redirect(url_for('deploy.deploy'))

    #回滚状态直接到更新中
    rollback_status = 3

    #如果更新是整站(0)，则type为整站回滚(2)
    if deploy_batch.type == 0:
        rollback_type = 2
    #如果更新是增量(1)，则type为增量回滚(3)
    elif deploy_batch.type == 1:
        rollback_type = 3

    #回滚批次号基于更新批次号，替换大写字母U(更新)为R(回滚)
    rollback_batch_no = deploy_batch.batch_no.replace('U', 'R')

    print "cese---cese"*10
    print rollback_batch_no
    print "cese---cese" * 10

    # #将更新内容写入文件
    # file_list1 = os.path.join(g.config.get('UPDATE_FILE_LIST'), deploy_batch.batch_no)
    #
    # #更新的文件变为回滚的文件
    # file_list = os.path.join(g.config.get('UPDATE_FILE_LIST'), rollback_batch_no)
    # # file_list_url = ''
    # # if len(form.content.data):
    # file_list_url = 'http://aud2.inzwc.com/filelist/' + rollback_batch_no
    #
    # shutil.copyfile("file_list1", "file_list")


    # #通过表单构建数据库插入记录
    # rollback_record = models.App_deploy_batch(batch_no=rollback_batch_no,
    #                                           app_id=deploy_batch.app_id,
    #                                           app_name=deploy_batch.app_name,
    #                                           type=rollback_type,
    #                                           status=rollback_status,
    #                                           env=deploy_batch.env,
    #                                           message_type=deploy_batch.message_type,
    #                                           restart_tomcat=deploy_batch.restart_tomcat,
    #                                           message_cc=deploy_batch.message_cc,
    #                                           desc=deploy_batch.batch_no + '回滚.',
    #                                           create_time=datetime.now(),
    #                                           launcher=g.user.account,
    #                                           # business_id=deploy_batch.business_id,
    #                                           # content=file_list_url,
    #                                           subject=deploy_batch.batch_no + '回滚.')

    #通过表单构建数据库插入记录
    rollback_record = models.App_deploy_batch(batch_no=rollback_batch_no,
                                              app_id=deploy_batch.app_id,
                                              app_name=deploy_batch.app_name,
                                              type=rollback_type,
                                              status=rollback_status,
                                              env=deploy_batch.env,
                                              message_type=deploy_batch.message_type,
                                              restart_tomcat=deploy_batch.restart_tomcat,
                                              message_cc=deploy_batch.message_cc,
                                              desc=deploy_batch.batch_no + '回滚.',
                                              create_time=datetime.now(),
                                              launcher=g.user.account,
                                              business_id=deploy_batch.business_id,
                                              subject=deploy_batch.batch_no + '回滚.')

    # print "我"*20
    # # print deploy_batch.business_id
    # print "你" * 20
    #写入数据库.
    rollback_record.save()

    #将更新批次号是否回滚置为1(是)
    deploy_batch.is_undo = 1
    deploy_batch.save()

    #daily测试环境更新
    if deploy_batch.env == 0:
        #根据环境，使用不同的Redis队列
        queue_name = 'daily'
    #project测试环境更新
    elif deploy_batch.env == 1:
        #根据环境，使用不同的Redis队列
        queue_name = 'project'
    #beta环境更新
    elif deploy_batch.env == 2:
        #根据环境，使用不同的Redis队列
        queue_name = 'beta'
    #生产环境更新
    elif deploy_batch.env == 3:
        # #根据环境，使用不同的Redis队列
        # queue_name = 'production1'
        if deploy_batch.business_id == 1 and redis_attrs.id == 1:
            host = redis_attrs.redis_ip
            port = redis_attrs.redis_port
            db = redis_attrs.redis_db
            beta_server = redis_attrs.beta_ip
            queue_name = 'production1'
            print "ppp" * 10
            print host
            print port
            print db
            print "%%%%" * 10
        elif deploy_batch.business_id == 2 and redis_attrs.id == 2:
            host = redis_attrs.redis_ip
            port = redis_attrs.redis_port
            db = redis_attrs.redis_db
            beta_server = redis_attrs.beta_ip
            queue_name = 'production1'
        elif deploy_batch.business_id == 3 and redis_attrs.id == 3:
            host = redis_attrs.redis_ip
            port = redis_attrs.redis_port
            db = redis_attrs.redis_db
            beta_server = redis_attrs.beta_ip
            queue_name = 'production1'
        elif deploy_batch.business_id == 4 and redis_attrs.id == 4:
            host = redis_attrs.redis_ip
            port = redis_attrs.redis_port
            db = redis_attrs.redis_db
            beta_server = redis_attrs.beta_ip
            queue_name = 'production1'
        elif deploy_batch.business_id == 5 and redis_attrs.id == 5:
            host = redis_attrs.redis_ip
            port = redis_attrs.redis_port
            db = redis_attrs.redis_db
            beta_server = redis_attrs.beta_ip
            queue_name = 'production1'


    #任务拆分
    nodes = models.App_nodes.query.with_entities(models.App_nodes.id, models.App_nodes.node_ip). \
        filter(models.App_nodes.node_id == models.App_servers.id,
               models.App_nodes.app_id == deploy_batch.app_id,
               models.App_servers.env == deploy_batch.env).all()

    #获取应用属性
    app_attrs = models.Apps.query.filter_by(id=deploy_batch.app_id).first()

    j = 0
    nodes_count = len(nodes)

    for node in nodes:

        j = j + 1

        #如果需要重启tomcat或全站回滚
        if int(deploy_batch.restart_tomcat) == 1 or rollback_type == 2:
            #如果节点数量超过2，则将节点分成2部分，第2部分延迟更新30秒
            if int(nodes_count / 2) == 0 or j <= int(nodes_count / 2):
                task_delay_time = 0
            else:
                task_delay_time = 30
        else:
            task_delay_time = 0

        #生成任务号task_no：md5(batch_no+节点IP+当前时间)
        task_no = hashlib.new("md5", rollback_batch_no + node.node_ip + str(datetime.now())).hexdigest()

        #创建节点任务插入记录
        task_record = models.App_deploy_node_task(task_no=task_no,
                                                  batch_id=rollback_record.id,
                                                  batch_no=rollback_batch_no,
                                                  node_id=node.id,
                                                  node_ip=node.node_ip,
                                                  status=0,
                                                  create_time=datetime.now())
        #写入数据库
        if task_record.save():
            #如果写入成功，任务加入redis队列
            #构建一个加入队列json数据
            task_dic = {
                "task_no": task_no,
                "app_name": app_attrs.app_name.strip(),
                "app_path": app_attrs.app_path.strip(),
                "tomcat_path": app_attrs.tomcat_path.strip(),
                "tomcat_port": app_attrs.port,
                "shutdown_port": app_attrs.shutdown_port,
                "batch_no": rollback_batch_no,
                "type": rollback_type,
                "restart_tomcat": deploy_batch.restart_tomcat,
                "node_ip": task_record.node_ip.strip(),
                # "rsync_path_name": app_attrs.rsync_path_name,
                "rsync_path_name": g.config.get('RSYNC_PATH_NAME')[app_attrs.rsync_path_name],
                "delay_time": task_delay_time,
                # "beta_server": app_attrs.beta_server
                "beta_server": redis_attrs.beta_ip,
                "business_id": redis_attrs.id
            }
            task_json = json.dumps(task_dic, skipkeys=True)

            # 增加任务到Redis队列
            q = RedisQueue(queue_name, host=host, port=port, db=db)
            q.put(task_json)

            # #增加任务到Redis队列
            # q = RedisQueue(queue_name, host=g.config.get('REDIS_HOST'), port=g.config.get('REDIS_PORT'),
            #                db=g.config.get('REDIS_DB'))
            # q.put(task_json)


            # #增加任务到Redis队列
            # q = RedisQueue(queue_name, host=g.config.get('REDIS_HOST'), port=g.config.get('REDIS_PORT'),
            #                db=g.config.get('REDIS_DB'))
            # q.put(task_json)

    #保存用户操作记录
    user_ac_record = models.User_ac_log(uid=g.user.uid,
                                        account=g.user.account,
                                        ip=g.user_real_ip,
                                        action='rollback',
                                        result=rollback_batch_no)
    #写入数据库
    user_ac_record.save()

    #重定向回应用页面
    return redirect(url_for('deploy.deploy'))


#任务日志ajax读取接口
@bp.route('/tasklog/', methods=['GET'])
@login_required
def tasklog():
    task_no = request.args.get('task_no')

    #日志文件目录
    tasklog = os.path.join(g.config.get('TASK_LOG_BASE_URL'), task_no + '.log')

    with open(tasklog, 'r') as file:
        tasklog_data = file.read()

    tasklog_data = tasklog_data.replace('\n', '<br>').replace(' ', '&nbsp').replace('[' + task_no + ']', '')

    return tasklog_data


#Tomcat日志ajax读取接口
@bp.route('/tomcatlog/', methods=['GET'])
@login_required
def tomcatlog():
    task_no = request.args.get('task_no')

    #日志文件目录
    tomcatlog = os.path.join(g.config.get('TOMCAT_LOG_BASE_URL'), task_no + '.log')

    stdout = os.popen("tail -100 " + tomcatlog)
    tomcatlog_data = ''.join(stdout.readlines())
    stdout.close()

    tomcatlog_data = tomcatlog_data.replace('\n', '<br>').replace(' ', '&nbsp')

    return tomcatlog_data


#更新文件列表读取接口
@bp.route('/updatefile/', methods=['GET'])
@login_required
def updatefile():
    batch_no = request.args.get('batch_no')

    updatefile = os.path.join(g.config.get('UPDATE_FILE_LIST'), batch_no)

    with open(updatefile, 'r') as file:
        updatefile_data = file.read()

    updatefile_data = updatefile_data.replace('\n', '<br>').replace(' ', '&nbsp')

    return updatefile_data


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


# 检查更新文件
@bp.route('/checkfilelist/', methods=['GET'])
@login_required
def checkfilelist():
    batch_no = request.args.get('batch_no')

    batch = models.App_deploy_batch.query.filter_by(batch_no=batch_no).first_or_404()
    app_attrs = models.Apps.query.filter_by(id=batch.app_id).first_or_404()

    beta_server = models.Business.query.filter_by(id=app_attrs.business_id).first()

    print "oo"*20
    # app.logger.debug('beta_server.beta_ip')
    print app_attrs.business_id
    print beta_server.beta_ip
    print "HHHH"*20

    # #执行检查文件列表脚本，并输出到stdout
    # stdout = os.popen(g.config.get('UPDATE_FILE_LIST_CHECK_SCRIPT') + ' ' + batch_no + ' ' + g.config.get(
    #     'RSYNC_USER') + ' ' + app.beta_server + ' ' + app.rsync_path_name)

    print g.config.get('UPDATE_FILE_LIST_CHECK_SCRIPT')
    print batch_no
    print g.config.get('RSYNC_USER')
    print g.config.get('RSYNC_PATH_NAME')[app_attrs.rsync_path_name]

    #执行检查文件列表脚本，并输出到stdout
    #注意beta_ip是结合业务id从business表中查询得到的
    #RSYNC_PATH_NAME 之前是 str 类型，后来改成了int类型，所以需要多一层转换
    stdout = os.popen(g.config.get('UPDATE_FILE_LIST_CHECK_SCRIPT') + ' ' + batch_no + ' ' + g.config.get('RSYNC_USER') + ' ' + beta_server.beta_ip + ' ' + g.config.get('RSYNC_PATH_NAME')[app_attrs.rsync_path_name])

    print "HHHH" * 20
    # print g.config.get('UPDATE_FILE_LIST_CHECK_SCRIPT') + ' ' + batch_no + ' ' + g.config.get('RSYNC_USER') + ' ' + beta_server.beta_ip + ' ' + app_attrs.rsync_path_name

    checklog_data = ''.join(stdout.readlines())
    stdout.close()

    #如果文件列表检查通过，修改file_check为1
    if checklog_data.find('UpdateFileListCheckOK') >= 0:
        batch.file_check = 1
        batch.save()

    #回车符和空格替换
    checklog_data = checklog_data.replace('\n', '<br>').replace(' ', '&nbsp')

    return checklog_data


#更新进度查询
@bp.route('/deploygo/<batch_no>', methods=['GET', 'POST'])
@login_required
def deploygo(batch_no):
    batch = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.batch_no,
                                                        models.App_deploy_batch.id,
                                                        models.App_deploy_batch.subject,
                                                        models.App_deploy_batch.app_id,
                                                        models.App_deploy_batch.app_name,
                                                        models.App_deploy_batch.plan,
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
                                                        models.App_deploy_batch.business_id,
                                                        models.App_deploy_batch.launcher,
                                                        models.Users.username).filter(
        models.App_deploy_batch.batch_no == batch_no,
        models.App_deploy_batch.launcher == models.Users.account).first_or_404()

    #数据库查询对象转换为字典
    object = batch._asdict()

    #替换文本中的换行符
    if object.get('content'):
        object['content'] = object.get('content').replace('\r\n', '<br/>')
    if object.get('desc'):
        object['desc'] = object.get('desc').replace('\r\n', '<br/>')

    #部署服务器列表
    node_list = models.App_deploy_node_task.query.filter_by(batch_no=batch_no).all()

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

    #获取抄送人名单
    mesg_cc_list = [(a.account, a.username) for a in models.Users_role.query.with_entities(models.Users_role.username,
                                                                                           models.Users_role.account).filter(
        models.Users_role.account.in_(batch.message_cc.split(',')))]
    mesg_cc_dict = dict(mesg_cc_list)

    return render_template('deploy/deploygo.html',
                           object=object,
                           node_list=node_list,
                           remark_list=remark_list,
                           APP_ENV=g.config.get('APP_ENV'),
                           DEPLOY_PLAN=g.config.get('DEPLOY_PLAN'),
                           BUSSINESS_TYPE=g.config.get('BUSSINESS_TYPE'),
                           NODE_TASK_STATUS=g.config.get('NODE_TASK_STATUS'),
                           DEPLOY_STATUS=g.config.get('DEPLOY_STATUS'),
                           DEPLOY_TYPE=g.config.get('DEPLOY_TYPE'),
                           MESSAGE_TYPE=g.config.get('MESSAGE_TYPE'),
                           ac_list=ac_list,
                           USER_ACTION_CONVERT=g.config.get('USER_ACTION_CONVERT'),
                           manager_dict=manager_dict,
                           mesg_cc_dict=mesg_cc_dict)


#提交更新批次备注
@bp.route('/batch_remark/<batch_id>', methods=['POST'])
@login_required
def batch_remark(batch_id):
    if not request.form.get('remark_content'):
        abort(400)

    remark_content = request.form.get('remark_content')
    remark_record = models.Deploy_batch_remarks(batch_id=batch_id,
                                                uid=g.user.uid,
                                                content=remark_content)
    remark_record.save()
    batch = models.App_deploy_batch.query.filter_by(id=batch_id).first_or_404()

    return redirect(url_for('deploy.deploygo', batch_no=batch.batch_no))


#接口：修改更新任务状态
@bp.route('/api/v1.0/node_task/modify_status/<task_no>', methods=['POST'])
def modify_node_task_status(task_no):
    # if not request.json or not 'status' in request.json:
    #     abort(400)
    print "bb" * 20

    #查询任务并修改任务状态
    record = models.App_deploy_node_task.query.filter_by(task_no=task_no).first()
    print "bb"*20
    print record.status
    print "bb" * 20
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


#更新历史列出查询
@bp.route('/his', methods=['GET', 'POST'])
@bp.route('/his/<int:page>', methods=['GET', 'POST'])
@bp.route('/his/<account>', methods=['GET', 'POST'])
@login_required
def deploy_his(page=1, account=None):
    form = SearchSiteForm()

    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        object_list = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.batch_no,
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
                                                                  models.Users.username).filter(
            models.App_deploy_batch.launcher == models.Users.account, 'app_name' + filter_string).order_by(
            desc(models.App_deploy_batch.create_time)).limit(50).all()

        #object_list = models.App_deploy_batch.query.filter('app_name' + filter_string).order_by(desc(models.App_deploy_batch.create_time)).limit(50).all()

        return render_template('deploy/deploy_his.html',
                               object_list=object_list,
                               form=form,
                               APP_ENV=g.config.get('APP_ENV'),
                               DEPLOY_STATUS=g.config.get('DEPLOY_STATUS'),
                               DEPLOY_TYPE=g.config.get('DEPLOY_TYPE'))
    else:

        if account:
            total = models.App_deploy_batch.query.filter(models.App_deploy_batch.launcher == account).count()
            object_list = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.batch_no,
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
                                                                      models.Users.username).filter(
                models.App_deploy_batch.launcher == models.Users.account,
                models.App_deploy_batch.launcher == account).order_by(
                desc(models.App_deploy_batch.create_time)).all()

            return render_template('deploy/deploy_his.html',
                                   total=total,
                                   object_list=object_list,
                                   form=form,
                                   APP_ENV=g.config.get('APP_ENV'),
                                   DEPLOY_STATUS=g.config.get('DEPLOY_STATUS'),
                                   DEPLOY_TYPE=g.config.get('DEPLOY_TYPE'))

        else:
            total = models.App_deploy_batch.query.count()
            paginate = models.App_deploy_batch.query.with_entities(models.App_deploy_batch.batch_no,
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
                                                                   models.Users.username).filter(
                models.App_deploy_batch.launcher == models.Users.account).order_by(
                desc(models.App_deploy_batch.create_time)).paginate(page, g.config.get('POSTS_PER_PAGE'), False)

            #paginate = models.App_deploy_batch.query.order_by(desc(models.App_deploy_batch.create_time)).paginate(page, config.POSTS_PER_PAGE, False)
            object_list = paginate.items

            pagination = models.App_deploy_batch.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))

            return render_template('deploy/deploy_his.html',
                                   total=total,
                                   pagination=pagination,
                                   object_list=object_list,
                                   form=form,
                                   APP_ENV=g.config.get('APP_ENV'),
                                   DEPLOY_STATUS=g.config.get('DEPLOY_STATUS'),
                                   DEPLOY_TYPE=g.config.get('DEPLOY_TYPE'))

# # 编辑应用
# @bp.route('/editapp/', methods=['GET', 'POST'])
# @bp.route('/editapp/<int:appid>', methods=['GET', 'POST'])

# #执行更新
# @bp.route('/dodeploy/<batch_no>', methods=['GET', 'POST'])
# #@login_required
# def dodeploy(batch_no):
#     deploy_batch = models.App_deploy_batch.query.filter_by(batch_no=batch_no).first_or_404()
#
#     #获取redis相关信息
#     # redis_attrs = models.Business.query.filter_by(id=deploy_batch.business_id).first()
#
#     redis_attrs = models.Business.query.filter_by(id=deploy_batch.business_id).first()


# Tomcat操作任务状态返回接口
#接口：修改更新任务状态
@bp.route('/api/v1.0/tomcat_task/modify_status/<task_no>', methods=['POST'])
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

    #json格式返回任务号和修改状态，返回码202
    return jsonify({'task_no': task_no, 'status': record.status}), 202


