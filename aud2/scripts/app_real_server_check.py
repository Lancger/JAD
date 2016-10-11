#!/home/www/.demo/bin/python
# -*- coding: utf-8 -*-
# #coding=utf-8
__author__ = 'lancger'
'''
该脚本比对更新发布系统中各项目所配置的应用服务器，连接IP和应用端口测试
'''

import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))
reload(sys)
sys.setdefaultencoding('utf-8')

from sets import Set
# from app.models import Apps, App_nodes
from app import create_app
# from ..models import Apps, App_nodes, db
from app.models import Apps, App_nodes, db
from config import default
import socket


app = create_app()
db.app=app
db.init_app(app)

NORMAL=0  
ERROR=1  
TIMEOUT=5 

app_count=0
port_count=[0]
port_error_count=[0]

def tcp_port_ping(ip,port,timeout=TIMEOUT):  
    try:  
        cs=socket.socket(socket.AF_INET,socket.SOCK_STREAM)  
        address=(str(ip),int(port))  
        status = cs.connect_ex((address))  
        cs.settimeout(timeout)  
        if status != NORMAL:  
            return ERROR  
        else:  
            return NORMAL      
    except Exception ,e:  
        print ERROR  
        print "error:%s" %e  
        return ERROR  
      
    return NORMAL


def app_real_server_check(app_name):
    '''
    项目本地配置真实服务器运行检查
    '''

    if Apps.query.with_entities(Apps.port).filter(Apps.app_name==app_name).first():
        #查询应用部署节点列表
        app_config_server_list = [(a.node_ip.encode('utf-8')) for a in App_nodes.query.with_entities(App_nodes.node_ip).filter(App_nodes.app_name==app_name).all()]

        #查询应用端口配置
        app_config_port = int(Apps.query.with_entities(Apps.port).filter(Apps.app_name==app_name).first()[0])

        #调试输出
        #print app_config_server_list
        #print app_config_port
	
        print ("%-30s port:%-20s" % (app_name,app_config_port)),
	check_result=0
	for ip in app_config_server_list:
	    port_count[0] = port_count[0] + 1
	    if tcp_port_ping(ip,app_config_port) == 1:
		check_result=1
	        port_error_count[0]=port_error_count[0]+1
                print '' 
                print ("    IP：%s,[端口连通检查异常]" % ip)

	if check_result == 0:
            print '[所有IP端口连通检查OK]' 
            

    else:
        print "应用不存在"


#获取所有应用列表
app_list = [(a.app_name.encode('utf-8')) for a in Apps.query.with_entities(Apps.app_name).filter(Apps.rsync_path_name=='www').all()]


print '开始检查更新发布系统项目部署服务器同真实服务器运行情况:'
for app in app_list:
    app_real_server_check(app)
    app_count += 1
print '检查完成!检查应用数：%s，检查端口数：%s, 异常端口数：%s' % (app_count,port_count[0],port_error_count[0])
