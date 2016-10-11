# coding: utf-8
__author__ = 'lancger'

from .. import models
from flask import render_template, request, redirect, url_for, Blueprint, flash, g, current_app
from ..forms import ChangeRoleform
from flask.ext.login import login_required
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users
from ..utils.ldap_handle import openldap_conn_open
from sqlalchemy import distinct
# from ..permissions import SSPermission
from ..permissions import UserPermission, DeveloperPermission, AuditorPermission, SAPermission, AdminPermission

bp = Blueprint('perm', __name__)



#列出角色
@bp.route('/roles', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def roles():
    object_list = models.Roles.query.order_by(models.Roles.id).all()
    return render_template('perm/roles.html', object_list=object_list)

#修改用户角色
@bp.route('/editrole/<uid>', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def editrole(uid):
    form = ChangeRoleform()
    form_sorce = models.Users_role.query.filter_by(uid=uid).first()

    if request.method == "GET":
        form.role.data = form_sorce.role_id

        form.role.choices = [(item, g.config.get('USER_ROLES')[item]) for item in
                             range(len(g.config.get('USER_ROLES')))]

    if request.method == "POST":
        form_sorce.role_id = form.role.data

        if form_sorce.save():
            #保存用户操作记录
            user_ac_record = models.User_ac_log(uid=g.user.uid,
                                                account=g.user.account,
                                                ip=g.user_real_ip,
                                                action='editrole',
                                                result=uid)
            #写入数据库
            user_ac_record.save()

        return redirect(url_for('user.users'))

    return render_template('perm/editrole.html', form=form, item=form_sorce)