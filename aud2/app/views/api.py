# coding=utf-8

import json
from flask import request, make_response, Blueprint,flash
from app.models.business import *
from app.models.self import *
from flask_wtf.csrf import CsrfProtect
from app.models import db
from app.utils import data_check_sign

csrf = CsrfProtect()

bp = Blueprint('api', __name__)
# csrf.exempt(bp)

# bp = Blueprint('api', )
# GET获取通过business_name获取该业务的配置和redis的信息
@bp.route('/v1.0/business/list_conf/<business_name>', methods=['GET'])
def v10_business_list(business_name):
    print "ok"
    db_data = Business.query.filter_by(business_name = business_name).first()
    business_name = db_data.business_name
    desc = db_data.desc
    beta_ip = db_data.beta_ip
    redis_ip = db_data.redis_ip
    redis_port = db_data.redis_port
    redis_db = db_data.redis_db
    business_data = {business_name:{'business_name':business_name,
                              'desc':desc,
                              'beta_ip':beta_ip,
                              'redis_ip':redis_ip,
                              'redis_port':redis_port,
                              'redis_db':redis_db
                            }}
    response = make_response(json.dumps(business_data))
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response


# GET获取通过business_id获取该业务的配置和redis的信息
@bp.route('/v1.0/redis/list_conf/<business_id>', methods=['GET'])
def v10_redis_id(business_id):
    print "ok"
    db_data = Business.query.filter_by(id = business_id).first()
    business_name = db_data.business_name
    desc = db_data.desc
    beta_ip = db_data.beta_ip
    redis_ip = db_data.redis_ip
    redis_port = db_data.redis_port
    redis_db = db_data.redis_db
    business_data = {business_id:{'business_name':business_name,
                              'desc':desc,
                              'beta_ip':beta_ip,
                              'redis_ip':redis_ip,
                              'redis_port':redis_port,
                              'redis_db':redis_db
                            }}
    response = make_response(json.dumps(business_data))
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response


# POST根据CMDB提交的业务数据，写入到数据库
#@csrf.exempt
@bp.route('/v1.0/business/add', methods=['POST'])
@csrf.exempt
def add_business():
    if not request.json or not 'business_name' in request.json:
        abort(400)

    business_name = request.json.get('business_name')
    print business_name
    try:
        bussiness_info = Business.query.filter_by(business_name = business_name).first()
        print bussiness_info.business_name
        if bussiness_info.business_name != None:
            flash('业务已经存在')
            return '{"status": "false"}'
    except:
        print "ok"

    db.session.add(Business(
        business_name = request.json.get('business_name'),
        desc = request.json.get('desc'),
        beta_ip = request.json.get('beta_ip'),
        redis_ip=request.json.get('redis_ip'),
        redis_port=request.json.get('redis_port'),
        redis_db=request.json.get('redis_db'),
    ))

    db.session.commit()
    return '{"status": "ok"}'


# # POST根据CMDB提交的应用数据，写入到数据库
# #@csrf.exempt
# @bp.route('/v1.0/app/add', methods=['POST'])
# @csrf.exempt
# def add_app():
#     if not request.json or not 'app_name' in request.json:
#         abort(400)
#
#     app_name = request.json.get('app_name')
#     print app_name
#     try:
#         app_info = Apps.query.filter_by(app_name = app_name).first()
#         print app_info.app_name
#         if app_info.app_name != None:
#             flash('应用已经存在')
#             return '{"status": "false"}'
#     except:
#         print "ok"
#
#     db.session.add(Apps(
#         app_name = request.json.get('app_name'),
#         status = request.json.get('status'),
#         app_path = request.json.get('app_path'),
#         tomcat_path=request.json.get('tomcat_path'),
#         shutdown_port=request.json.get('shutdown_port'),
#         port=request.json.get('port'),
#         # site=request.json.get('site'),
#         rsync_path_name=request.json.get('rsync_path_name'),
#         # svn_url=request.json.get('svn_url'),
#         # mvn_command=request.json.get('mvn_command'),
#         # java_opts=request.json.get('java_opts'),
#         # desc=request.json.get('desc'),
#         # node=request.json.get('node'),
#         business_id=request.json.get('business_id')
#     ))
#
#     db.session.commit()
#     return '{"status": "ok"}'


# POST根据CMDB提交的应用数据，写入到数据库
#@csrf.exempt
@bp.route('/v1.0/app/add', methods=['POST'])
@csrf.exempt
def add_app():
    sign_data = request.json.get('sign_data')
    print sign_data
    print type(sign_data)    #注意传递过来的数据类型需要是字符型的
    sign = request.json.get('sign', '')
    print sign
    print "*" * 50
    print type(json.dumps(sign_data))
    if not sign_data or not sign:
        return '{}', 400
    if not data_check_sign(sign_data, sign, 'cmdb.inzwc.com'):
        return '{}', 403
    sign_data = json.loads(sign_data)
    app_name = sign_data.get('app_name')
    print app_name
    try:
        app_info = Apps.query.filter_by(app_name = app_name).first()
        print app_info.app_name
        if app_info.app_name != None:
            flash('应用已经存在')
            return '{"status": "false"}'
    except:
        print "ok"
	print sign_data.get('business_id')

    db.session.add(Apps(
        app_name = sign_data.get('app_name'),
        status = sign_data.get('status'),
        app_path = sign_data.get('app_path'),
        tomcat_path=sign_data.get('tomcat_path'),
        shutdown_port=sign_data.get('shutdown_port'),
        port=sign_data.get('port'),
        site=sign_data.get('site'),
        rsync_path_name=sign_data.get('rsync_path_name'),
        svn_url=sign_data.get('svn_url'),
        mvn_command=sign_data.get('mvn_command'),
        java_opts=sign_data.get('java_opts'),
        desc=sign_data.get('desc'),
        #node=sign_data.get('node'),
        business_id=int(sign_data.get('business_id',0))
	#business_id=1
    ))

    db.session.commit()
    return '{"status": "ok"}'


# GET获取通过site_name获取该站点的详细信息
@bp.route('/v1.0/site/list/<site_name>', methods=['GET'])
def v10_site_name(site_name):
    print "ok"
    db_data = App_sites.query.filter_by(site_name = site_name).first()
    site_name = db_data.site_name
    id = db_data.id
    site_data = {site_name:{'site_name':site_name,
                              'id':id
                            }}
    response = make_response(json.dumps(site_data, ensure_ascii=False))
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response

# GET获取通过site_id获取该站点的详细信息
@bp.route('/v1.0/site/list_conf/<site_id>', methods=['GET'])
def v10_site_id(site_id):
    print "ok"
    db_data = App_sites.query.filter_by(id = site_id).first()
    site_name = db_data.site_name
    id = db_data.id
    site_data = {id:{'site_name':site_name,
                              'id':id
                            }}
    response = make_response(json.dumps(site_data, ensure_ascii=False))
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response

# GET获取通过site_name获取该站点的详细信息
@bp.route('/v1.0/site/list', methods=['GET'])
def v10_site_list():
    print "ok"

    db_date = App_sites.query.all()
    print db_date
    print "ok"
    site_data = {}
    for value in db_date:
        item = {}
        site_name = value.site_name
        item['site_name'] = value.site_name
        item['id'] = value.id

        site_data[site_name] = item

    response = make_response(json.dumps(site_data, ensure_ascii=False))
    # response = make_response(json.dumps(site_data))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
