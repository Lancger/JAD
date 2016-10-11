# coding: utf-8
__author__ = 'lancger'

from flask import render_template, request, redirect, url_for, Blueprint, current_app
from flask.ext.login import login_required
from ..models import Business, User_business, App_sites, App_deploy_node_task, Deploy_batch_remarks, App_deploy_node_info, App_deploy_batch, User_ac_log, Message_log, App_tomcat_his, Roles, Users_role,  Apps, App_servers, App_nodes, System, Users
from sqlalchemy import or_
from ..forms import UserSearchForm, ChangeRoleform
from ..permissions import AdminPermission

bp = Blueprint('system', __name__)


@bp.route('/users/list', methods=['GET', 'POST'])
@bp.route('/users/list/<int:page>', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def users(page=1):
    """
    列出系统用户
    """
    form = UserSearchForm()

    if request.method == "POST":
        filter_string = '%' + form.s_content.data + '%'
        items = LDAP_User.query.with_entities(LDAP_User.uidnumber,
                                              LDAP_User.cn,
                                              LDAP_User.sn,
                                              LDAP_User.mobile,
                                              LDAP_User.mail,
                                              LDAP_User.depart,
                                              Sys_Roles.id,
                                              Sys_Roles.role).filter(
            Sys_Users_Role.uid == LDAP_User.uidnumber).filter(Sys_Users_Role.role_id == Sys_Roles.id).filter(
            or_((LDAP_User.cn.like(filter_string)), (LDAP_User.sn.like(filter_string)))).all()

        total = len(items)
        return render_template('system/users.html', total=total, object_list=items, form=form)
    else:
        config = current_app.config

        paginate = LDAP_User.query.with_entities(LDAP_User.uidnumber,
                                                 LDAP_User.cn,
                                                 LDAP_User.sn,
                                                 LDAP_User.mobile,
                                                 LDAP_User.mail,
                                                 LDAP_User.depart,
                                                 Sys_Roles.id,
                                                 Sys_Roles.role).filter(
            Sys_Users_Role.uid == LDAP_User.uidnumber).filter(Sys_Users_Role.role_id == Sys_Roles.id).order_by(
            LDAP_User.uidnumber).paginate(page, config.get('POSTS_PER_PAGE'), False)
        object_list = paginate.items
        total = len(object_list)

        pagination = LDAP_User.query.paginate(page, per_page=config.get('POSTS_PER_PAGE'))

        return render_template('system/users.html', total=total, pagination=pagination, object_list=object_list,
                               form=form)


@bp.route('/roles/list', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def roles():
    """
    列出角色
    """
    object_list = Sys_Roles.query.order_by(Sys_Roles.id).all()
    return render_template('system/roles.html', object_list=object_list)


@bp.route('/roles/<int:role_id>/users', methods=['GET'])
@login_required
@AdminPermission()
def role_users(role_id):
    """
    列出角色下的用户
    """
    object_list = LDAP_User.query.with_entities(LDAP_User.uidnumber,
                                                LDAP_User.cn,
                                                LDAP_User.sn,
                                                LDAP_User.mobile,
                                                LDAP_User.mail,
                                                LDAP_User.depart,
                                                Sys_Roles.id,
                                                Sys_Roles.role).filter(
        Sys_Users_Role.uid == LDAP_User.uidnumber).filter(Sys_Users_Role.role_id == Sys_Roles.id,
                                                          Sys_Users_Role.role_id == role_id).order_by(
        LDAP_User.uidnumber).all()
    total = len(object_list)

    return render_template('system/role_users.html', object_list=object_list, total=total)


@bp.route('/user/<uid>/edit', methods=['GET', 'POST'])
@login_required
@AdminPermission()
def user_change_role(uid):
    """
    修改用户角色
    """
    form = ChangeRoleform()
    form_sorce = Sys_Users_Role.query.filter_by(uid=uid).first()

    config = current_app.config

    if request.method == "GET":
        form.role.data = form_sorce.role_id

        form.role.choices = [(item, config.get('USER_ROLES')[item]) for item in
                             range(len(config.get('USER_ROLES')))]

    if request.method == "POST":
        form_sorce.role_id = form.role.data

        if form_sorce.save():
            # #保存用户操作记录
            # user_ac_record = models.User_ac_log(uid=g.user.uid,
            #                                    account=g.user.account,
            #                                    ip=g.user_real_ip,
            #                                    action='editrole',
            #                                    result=uid)
            ##写入数据库
            #user_ac_record.save()
            pass

        return redirect(url_for('system.users'))

    return render_template('system/editrole.html', form=form, item=form_sorce)
