#!/home/www/.demo/bin/python
# -*- coding: utf-8 -*-
# #coding=utf-8
__author__ = 'lancger'
'''
该脚本比对更新发布系统中各项目所配置的应用服务器，和nginx实际配置upstream server比较测试
'''

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))
reload(sys)
sys.setdefaultencoding('utf-8')

from sets import Set
# from app.models import Apps, App_nodes
# from ..models import Apps, App_nodes
from app import create_app
from app.models import Apps, App_nodes, db
from config import default
import urllib2


app = create_app()
db.app=app
db.init_app(app)

def app_distribution_upstream_check(app_name):
    '''
    项目本地配置同nginx upstream配置检查
    '''

    if Apps.query.with_entities(Apps.port).filter(Apps.app_name==app_name).first():
        #查询应用部署节点列表
        app_config_server_list = [(a.node_ip.encode('utf-8')) for a in App_nodes.query.with_entities(App_nodes.node_ip).filter(App_nodes.app_name==app_name).all()]

        #查询应用端口配置
        app_config_port = int(Apps.query.with_entities(Apps.port).filter(Apps.app_name==app_name).first()[0])

        #调试输出
        #print app_config_server_list
        #print app_config_port


        #从接口获取应用部署服务器列表和服务端口
        response = urllib2.urlopen(default.Config.WAF_UPSTREAM_GET_APP_SERVER_API+app_name)
        data = response.read()
        if "server" in data:
            #后端服务器IP列表
            upstream_server_list = [(x.split(' ')[1].split(':')[0]) for x in data.split('\n') if x]
            #应用端口
            server_port = int(data.split('\n')[0].split(':')[1])

            #调试输出
            #print upstream_server_list
            #print server_port
            #print Set(app_config_server_list).symmetric_difference(Set(upstream_server_list))

            #检查更新发布系统配置同nginx upstream实际配置
            if len(Set(app_config_server_list).symmetric_difference(Set(upstream_server_list)))==0:
                print ("%-30s%s" % (app_name,'[服务器列表检查OK]')),
                if app_config_port == server_port:
                    print ("%s" % '[端口:'+str(server_port)+'检查一致]')
                else:
                    print ("%s" % '[端口检查不一致，本地：'+str(app_config_port)+'nginx:'+str(server_port)+']')
            else:
                print ("%-30s%s" % (app_name,'[服务器列表检查不一致]')),
                if app_config_port == server_port:
                    print ("%s" % '[端口:'+str(server_port)+'检查一致]')
                else:
                    print ("%s" % '[端口检查不一致，本地：'+str(app_config_port)+'nginx:'+str(server_port)+']')
                print ("    本地：%s" % app_config_server_list)
                print ("    nginx：%s" % upstream_server_list)

        else:
            print ("%-30s" % app_name),
            print data

    else:
        print "应用不存在"


#获取所有应用列表
app_list = [(a.app_name.encode('utf-8')) for a in Apps.query.with_entities(Apps.app_name).filter(Apps.rsync_path_name=='www').all()]

print '开始检查更新发布系统项目部署服务器同nginx upstream server配置:'
for app in app_list:
    app_distribution_upstream_check(app)
