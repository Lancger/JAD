# coding: utf-8
__author__ = 'lancger'

import json
import hashlib
from datetime import datetime
from .. import models
from flask import render_template, request, redirect, url_for, Blueprint, flash, g, current_app
from flask.ext.login import login_user, logout_user, login_required
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users
from sqlalchemy import or_, desc, func, exists
#from ..forms import LoginForm
from ..forms import SearchSiteForm, UserSearchForm, addUserForm
from ..utils.ldap_handle import openldap_conn_open, ad_conn_open, DeptConvertToDn, dnConvertToDept
from ..utils.ldap_sync_user import ldapConnOpen, ldapHandle
# from ..permissions import SSPermission, AdminPermission
from ..permissions import UserPermission, DeveloperPermission, AuditorPermission, SAPermission, AdminPermission


bp = Blueprint('user', __name__)

#同步ldap用户信息
@bp.route('/ldapusersync', methods=['GET'])
#@login_required
#@AdminPermission()
def ldapsync():
    #实例化utils.ldapHandle，连接好ldap，并准备好接受查询
    print "++++++++++++"
    ldap_conn = ldapConnOpen()

    #获取所有cn数据，并存入数据库对应表中
    #result = ldap_conn.ldap_get_all_user(search_base_dn='ou=技术中心,ou=中网彩,dc=aicai,dc=com')
    result = ldap_conn.ldap_get_all_user(search_base_dn='ou=中网彩,dc=aicai,dc=com')
    print result

    if result:
        #先清空Users表中所有数据
        models.Users.query.delete()
        print "shanchu chenggong"

        #将同步过来的数据入库
        for item in result:
            #通过dn生成部门如:中网彩\技术中心\系统运维部
            depart = dnConvertToDept(item.get('cn'), item.get('dn'))

            #构建插入记录
            record = models.Users(dn=item.get('dn').decode('utf8'),
                                  username=item.get('sn').decode('utf8'),
                                  account=item.get('uid'),
                                  uid=item.get('uidNumber'),
                                  mobile=item.get('mobile'),
                                  email=item.get('mail'),
                                  depart=depart)
            record.save()


        new_user_list = [(a.uid, a.account, a.username) for a in
                         models.Users.query.filter(~exists().where(models.Users_role.uid == models.Users.uid))]

        for user in new_user_list:
            ur_record = models.Users_role(uid=int(user[0]),
                                          account=user[1],
                                          username=user[2],
                                          role_id=1)  #默认角色只能登录
            ur_record.save()

        print 'ldap用户同步成功'

        #保存用户操作记录
        user_ac_record = models.User_ac_log(uid=g.user.uid,
                                            account=g.user.account,
                                            ip=g.user_real_ip,
                                            action='ldapsync',
                                            result='True')
        #写入数据库
        user_ac_record.save()

    else:
        #保存用户操作记录
        user_ac_record = models.User_ac_log(uid=g.user.uid,
                                            account=g.user.account,
                                            ip=g.user_real_ip,
                                            action='ldapsync',
                                            result='False')
        #写入数据库
        user_ac_record.save()

        print 'ldap用户同步失败'

    #关闭ldap连接
    ldap_conn.ldap_conn_close()

    return redirect(url_for('user.users'))


#列出用户
@bp.route('/list', methods=['GET', 'POST'])
@bp.route('/list/<int:page>', methods=['GET', 'POST'])
def users(page=1):
    form = SearchSiteForm()
    if request.method == "POST":
        filter_string = '%' + form.s_content.data + '%'
        items = models.Users.query.with_entities(models.Users.uid,
                                                 models.Users.account,
                                                 models.Users.username,
                                                 models.Users.mobile,
                                                 models.Users.email,
                                                 models.Users.depart,
                                                 models.Roles.id,
                                                 models.Roles.role).filter(
            models.Users_role.uid == models.Users.uid).filter(models.Users_role.role_id == models.Roles.id).filter(
            or_((models.Users.account.like(filter_string)), (models.Users.username.like(filter_string)))).all()

        total = len(items)
        return render_template('user/users.html', total=total, object_list=items, form=form)
    else:
        total = models.Users.query.count()
        paginate = models.Users.query.with_entities(models.Users.uid,
                                                    models.Users.account,
                                                    models.Users.username,
                                                    models.Users.mobile,
                                                    models.Users.email,
                                                    models.Users.depart,
                                                    models.Roles.id,
                                                    models.Roles.role).filter(
            models.Users_role.uid == models.Users.uid).filter(models.Users_role.role_id == models.Roles.id).order_by(
            models.Users.uid).paginate(page, g.config.get('POSTS_PER_PAGE'), False)
        object_list = paginate.items


        pagination = models.Users.query.paginate(page, per_page=g.config.get('POSTS_PER_PAGE'))

        return render_template('user/users.html', total=total, pagination=pagination, object_list=object_list, form=form)


#列出角色下的用户
@bp.route('/users_role/<role_id>', methods=['GET'])
@login_required
@AdminPermission()
def users_role(role_id):
    object_list = models.Users.query.with_entities(models.Users.uid,
                                                   models.Users.account,
                                                   models.Users.username,
                                                   models.Users.mobile,
                                                   models.Users.email,
                                                   models.Users.depart,
                                                   models.Roles.id,
                                                   models.Roles.role).filter(
        models.Users_role.uid == models.Users.uid).filter(models.Users_role.role_id == models.Roles.id,
                                                          models.Users_role.role_id == role_id).order_by(
        models.Users.uid).all()
    total = len(object_list)

    return render_template('user/users_role.html', object_list=object_list, total=total)
