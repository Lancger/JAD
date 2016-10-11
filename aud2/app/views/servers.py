# coding: utf-8
__author__ = 'lancger'

from flask import render_template, request, redirect, url_for, Blueprint, flash, g, \
    session, current_app
from .. import models
# from .. import app
import requests
import hashlib, json
from flask.ext.login import login_user, logout_user, login_required
from datetime import datetime, date, timedelta
from ..forms import LoginForm, SearchSiteForm, SearchServerForm, SearchAppForm, ServerAddFromCMDB, AddServerForm
#from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_action_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users
from sqlalchemy import desc, func
from ..utils.ldap_handle import openldap_conn_open
from ..utils.ldap_sync_user import ldapConnOpen, ldapHandle
# from ..permissions import SSPermission
from ..permissions import UserPermission, DeveloperPermission, AuditorPermission, SAPermission, AdminPermission

bp = Blueprint('servers', __name__)



#列出服务器(普通用户权限)
@bp.route('/l_servers', methods=['GET', 'POST'])
@bp.route('/l_servers/<int:page>', methods=['GET', 'POST'])
@login_required
def l_servers(page=1):
    form = SearchServerForm()
    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        filter_field = form.s_select.data
        items = models.App_servers.query.with_entities(models.App_servers.server_name,
                                                       models.App_servers.inner_ip,
                                                       models.App_servers.env,
                                                       models.App_servers.location,
                                                       models.App_servers.type,
                                                       models.App_servers.internet_ip,
                                                       models.App_servers.cpu,
                                                       models.App_servers.ram,
                                                       models.App_servers.hdd,
                                                       models.App_servers.status,
                                                       models.App_servers.desc,
                                                       func.group_concat(models.App_nodes.app_name).label('app_list')). \
            filter(models.App_servers.id == models.App_nodes.node_id). \
            group_by(models.App_servers.id). \
            order_by(models.App_servers.inner_ip).filter(filter_field + filter_string).all()

        total = len(items)
        return render_template('servers/l_servers.html',
                               total=total,
                               object_list=items,
                               form=form,
                               APP_ENV=g.config.get('APP_ENV'),
                               SERVER_LOCATION=g.config.get('SERVER_LOCATION'),
                               SERVER_TYPE=g.config.get('SERVER_TYPE'))
    else:

        paginate = models.App_servers.query.with_entities(models.App_servers.server_name,
                                                          models.App_servers.inner_ip,
                                                          models.App_servers.env,
                                                          models.App_servers.location,
                                                          models.App_servers.type,
                                                          models.App_servers.internet_ip,
                                                          models.App_servers.cpu,
                                                          models.App_servers.ram,
                                                          models.App_servers.hdd,
                                                          models.App_servers.status,
                                                          models.App_servers.desc,
                                                          func.group_concat(models.App_nodes.app_name).label(
                                                              'app_list')). \
            filter(models.App_servers.id == models.App_nodes.node_id). \
            group_by(models.App_servers.id). \
            order_by(models.App_servers.inner_ip).paginate(page, g.config.get('POSTS_PER_PAGE'), False)
        object_list = paginate.items
        total = models.App_servers.query.count()

        pagination = models.App_servers.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        return render_template('servers/l_servers.html',
                               total=total,
                               pagination=pagination,
                               object_list=object_list,
                               form=form,
                               APP_ENV=g.config.get('APP_ENV'),
                               SERVER_LOCATION=g.config.get('SERVER_LOCATION'),
                               SERVER_TYPE=g.config.get('SERVER_TYPE'))



#列出服务器
@bp.route('/servers', methods=['GET', 'POST'])
@bp.route('/servers/<int:page>', methods=['GET', 'POST'])
@login_required
def servers(page=1):
    form = SearchServerForm()
    if request.method == "POST":
        filter_string = ' like "%' + form.s_content.data + '%"'
        filter_field = form.s_select.data
        items = models.App_servers.query.filter(filter_field + filter_string).all()

        total = len(items)
        return render_template('servers/server.html',
                               total=total,
                               object_list=items,
                               form=form,
                               APP_ENV=g.config.get('APP_ENV'),
                               SERVER_LOCATION=g.config.get('SERVER_LOCATION'),
                               SERVER_TYPE=g.config.get('SERVER_TYPE'),
                               SERVER_STATUS=g.config.get('SERVER_STATUS'),
                               BUSSINESS_TYPE=g.config.get('BUSSINESS_TYPE'))
    else:
        total = models.App_servers.query.count()
        paginate = models.App_servers.query.order_by(models.App_servers.location, models.App_servers.inner_ip).paginate(
            page, g.config.get('POSTS_PER_PAGE'), False)
        object_list = paginate.items

        # #数据库中选择业务类别
        # form.business_id.choices = [(a.id, a.name) for a in \
        #                             models.Business.query.order_by(models.Business.name).all()]

        pagination = models.App_servers.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))
        return render_template('servers/server.html',
                               total=total,
                               pagination=pagination,
                               object_list=object_list,
                               form=form,
                               APP_ENV=g.config.get('APP_ENV'),
                               SERVER_LOCATION=g.config.get('SERVER_LOCATION'),
                               SERVER_TYPE=g.config.get('SERVER_TYPE'),
                               SERVER_STATUS=g.config.get('SERVER_STATUS'),
                               BUSSINESS_TYPE=g.config.get('BUSSINESS_TYPE'))



#手动增加服务器
@bp.route('/addserver', methods=['GET', 'POST'])
@login_required
@SAPermission()
def addserver():
    #构建一个添加应用表单
    form = AddServerForm()

    #服务器位置，0 公司机房，1 广州七星岗电信，2 广州沙溪电信，3 北京北显联通，4 深圳龙岗电信，5 阿里云杭州
    form.location.choices = [(item, g.config.get('SERVER_LOCATION')[item]) for item in
                             range(len(g.config.get('SERVER_LOCATION')))]
    #类别：0 测试环境，1 beta环境，2 生产环境
    form.env.choices = [(item, g.config.get('APP_ENV')[item]) for item in range(len(g.config.get('APP_ENV')))]
    #服务器类型，0 物理机，1，KVM虚拟机，2 LXC容器
    form.type.choices = [(item, g.config.get('SERVER_TYPE')[item]) for item in range(len(g.config.get('SERVER_TYPE')))]

    #服务器状态，(0 务器准备中',1'正常运行中',2'维护中',3'已下架',4'已报废')
    form.status.choices = [(item, g.config.get('SERVER_STATUS')[item]) for item in range(len(g.config.get('SERVER_STATUS')))]


    # #业务选择，(0 彩票业务, 1 金融业务 , 2 滴滴业务， 3 配资业务， 4 新增业务)
    # form.business_id.choices = [(item, g.config.get('BUSSINESS_TYPE')[item]) for item in range(len(g.config.get('BUSSINESS_TYPE')))]


    #数据库中选择业务类别
    form.business_id.choices = [(a.id, a.business_name) for a in \
                                    models.Business.query.order_by(models.Business.business_name).all()]

    if form.validate_on_submit():
        #通过表单构建数据库插入记录
        record = models.App_servers(server_name=form.server_name.data.strip(),
                                    inner_ip=form.inner_ip.data.strip(),
                                    env=form.env.data,
                                    location=form.location.data,
                                    type=form.type.data,
                                    internet_ip=form.internet_ip.data.strip(),
                                    cpu=int(form.cpu.data),
                                    ram=int(form.ram.data),
                                    hdd=int(form.hdd.data),
                                    status=form.status.data,
                                    desc=form.desc.data,
                                    business_id=form.business_id.data)
        #写入数据库
        if record.save():
            flash('服务器添加成功！')

            #保存用户操作记录
           # user_ac_record = models.User_action_log(uid=g.user.uid,
            #                                    account=g.user.account,
            #                                    ip=g.user_real_ip,
            #                                    action='addserver',
            #                                    result=record.inner_ip)
            #写入数据库
            #user_ac_record.save()

        #重定向回应用页面
        return redirect(url_for('servers.servers'))

    return render_template('servers/addserver.html', form=form)



# 通过cmdb列表增加服务器
@bp.route('/add', methods=['GET', 'POST'])
@login_required
@SAPermission()
def server_add():
    form = ServerAddFromCMDB()

    if request.method == "POST":
        for server in form.server_name.data:
            cmdb_server_info = requests.get(current_app.config.get('CMDB_GET_ONE_SERVER_API') + server)
            cmdb_server_dict = json.loads(cmdb_server_info.content)

            # 通过表单构建数据库插入记录
            record = models.App_servers(server_name=server,
                                        inner_ip=cmdb_server_dict[server]['lan_ip'],
                                        env=cmdb_server_dict[server].get('server_env', 3),
                                        location=cmdb_server_dict[server]['server_jifang_id'],
                                        type=cmdb_server_dict[server].get('server_type', 0),
                                        internet_ip=cmdb_server_dict[server]['server_pub_ip'],
                                        cpu=str(cmdb_server_dict[server].get('server_cpu_model', '0')) if
                                        cmdb_server_dict[
                                            server].get('server_cpu_model', '0') else '0' + '/' +
                                                                                      str(cmdb_server_dict[server].get(
                                                                                          'server_cpu_core', '0')) if
                                        cmdb_server_dict[server].get('server_cpu_core', '0') else '0',
                                        ram=cmdb_server_dict[server]['server_mem'],
                                        hdd=cmdb_server_dict[server]['server_harddisk'],
                                        status=cmdb_server_dict[server]['server_status'],
                                        desc=cmdb_server_dict[server]['server_assets_id'],
                                        business_id="1")
            # 写入数据库
            if record.save():
                flash('服务器添加成功!')

                # 保存用户操作记录
              #  user_ac_record = models.User_action_log(uid=g.user.uid,
               #                                     account=g.user.account,
                #                                    ip=g.user_real_ip,
               #                                     action='addserver',
                #                                    result=record.inner_ip)
                #写入数据库
                #user_ac_record.save()

        # 重定向回应用页面
        return redirect(url_for('servers.servers'))

    else:
        all_cmdb_server_list = requests.get(current_app.config.get('CMDB_GET_ALL_SERVER_API'))
        all_cmdb_server_dict = json.loads(all_cmdb_server_list.content)

        all_local_server_list = models.App_servers.query.all()

        # 从all_cmdb_server_dict中剔除已经在本地存在的服务器
        for server in all_local_server_list:
            if all_cmdb_server_dict.get(server.server_name):
                all_cmdb_server_dict.pop(server.server_name)

        form.server_name.choices = [(key, key) for key, value in all_cmdb_server_dict.iteritems()]

        # 排下序
        form.server_name.choices.sort()

    return render_template('servers/server_add.html', form=form)





#服务器详情
@bp.route('/serverdetail/', methods=['GET', 'POST'])
@bp.route('/serverdetail/<int:id>', methods=['GET', 'POST'])
@login_required
def serverdetail(id=0):
    #编辑服务器有2种方式：id和IP
    if id == 0 and request.args.get('ip'):
        #通过IP参数编辑服务器
        ip = request.args.get('ip')
        obj_sorce = models.App_servers.query.filter_by(inner_ip=ip)[0]
    else:
        #通过id参数编辑服务器
        obj_sorce = models.App_servers.query.filter_by(id=int(id))[0]

    if request.method == "GET":
        ##服务器位置，0 公司机房，1 广州七星岗电信，2 广州沙溪电信，3 北京北显联通，4 深圳龙岗电信，5 阿里云杭州
        #form.location.choices = [(item, SERVER_LOCATION[item]) for item in range(len(SERVER_LOCATION))]
        ##类别：0 测试环境，1 beta环境，2 生产环境
        #form.env.choices = [(item, APP_ENV[item]) for item in range(len(APP_ENV))]
        ##服务器类型，0 物理机，1，KVM虚拟机，2 LXC容器
        #form.type.choices = [(item, SERVER_TYPE[item]) for item in range(len(SERVER_TYPE))]

        items = models.App_nodes.query.filter_by(node_ip=obj_sorce.inner_ip).all()
        total = len(items)

    return render_template('servers/serverdetail.html',
                           object_list=items,
                           total=total,
                           obj=obj_sorce,
                           SERVER_TYPE=g.config.get('SERVER_TYPE'),
                           SERVER_LOCATION=g.config.get('SERVER_LOCATION'),
                           APP_ENV=g.config.get('APP_ENV'))

#删除服务器
'''
流程：
1.删除App_servers中的记录
2.删除App_nodes中的记录
'''

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
                user_ac_record = models.User_action_log(uid=0,
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

#编辑服务器
@bp.route('/editserver/', methods=['GET', 'POST'])
@bp.route('/editserver/<int:id>', methods=['GET', 'POST'])
@login_required
@SAPermission()
def editserver(id=0):
    form = AddServerForm()

    #编辑服务器有2种方式：id和IP
    if id == 0 and request.args.get('ip'):
        #通过IP参数编辑服务器
        ip = request.args.get('ip')
        form_sorce = models.App_servers.query.filter_by(inner_ip=ip)[0]
    else:
        #通过id参数编辑服务器
        form_sorce = models.App_servers.query.filter_by(id=int(id))[0]

    if request.method == "GET":
        form.server_name.data = form_sorce.server_name
        form.inner_ip.data = form_sorce.inner_ip
        form.internet_ip.data = form_sorce.internet_ip
        form.cpu.data = form_sorce.cpu
        form.ram.data = form_sorce.ram
        form.hdd.data = form_sorce.hdd
        form.type.data = form_sorce.type
        form.location.data = form_sorce.location
        form.env.data = form_sorce.env
        form.desc.data = form_sorce.desc
        form.business_id.data = form_sorce.business_id

        #app.logger.info('调试数据form.location.data:%s' % form.location.data)

        #服务器位置，0 公司机房，1 广州七星岗电信，2 广州沙溪电信，3 北京北显联通，4 深圳龙岗电信，5 阿里云杭州
        form.location.choices = [(item, g.config.get('SERVER_LOCATION')[item]) for item in
                                 range(len(g.config.get('SERVER_LOCATION')))]
        #类别：0 测试环境，1 beta环境，2 生产环境
        form.env.choices = [(item, g.config.get('APP_ENV')[item]) for item in range(len(g.config.get('APP_ENV')))]
        #服务器类型，0 物理机，1，KVM虚拟机，2 LXC容器
        form.type.choices = [(item, g.config.get('SERVER_TYPE')[item]) for item in
                             range(len(g.config.get('SERVER_TYPE')))]

        form.status.choices = [(item, g.config.get('SERVER_STATUS')[item]) for item in
                             range(len(g.config.get('SERVER_STATUS')))]

        #数据库中选择业务类别
        form.business_id.choices = [(a.id, a.business_name) for a in \
                                    models.Business.query.order_by(models.Business.business_name).all()]

        items = models.App_nodes.query.filter_by(node_ip=form_sorce.inner_ip).all()
        total = len(items)

    if request.method == "POST":
        form_sorce.server_name = form.server_name.data
        form_sorce.inner_ip = form.inner_ip.data.strip()
        form_sorce.internet_ip = form.internet_ip.data.strip()
        form_sorce.cpu = form.cpu.data
        form_sorce.ram = form.ram.data
        form_sorce.hdd = form.hdd.data
        form_sorce.type = form.type.data
        form_sorce.location = form.location.data
        form_sorce.env = form.env.data
        form_sorce.desc = form.desc.data
        form_sorce.business_id = form.business_id.data

        if form_sorce.save():
            # app.logger.info(form_sorce.name + form_sorce.username)

            #保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='editserver',
                                                result=form_sorce.inner_ip)
            #写入数据库
            user_ac_record.save()

        return redirect(url_for('servers.servers'))

    return render_template('servers/editserver.html', form=form, object_list=items, total=total)
