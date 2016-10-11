#!/usr/bin/env python
#coding: utf8
import paramiko
import hashlib, json
import redis
import time
import logging
import os
import requests
from multiprocessing import Pool

#获取本程序父路径
SCRIPT_PATH = os.path.abspath(os.path.dirname(__file__))
BASE_PATH = os.path.abspath(os.path.dirname(SCRIPT_PATH))
#日志保存路径
LOG_PATH = BASE_PATH + "/logs/updateOption.log"
#任务配置文件暂存路径
TASK_PATH = BASE_PATH + "/taskfile/"

#Beta rsync服务器地址
BETA_RSYNC_SERVER = '10.71.64.226'
#更新脚本本地暂存路径
DEPLOY_LOCAL = '/home/wwwupdate/autodeploy/scripts/deploy.sh'
#Tomcat脚本本地暂存路径
TOMCAT_LOCAL = '/home/wwwupdate/autodeploy/scripts/tomcat.sh'
#更新脚本部署父路径
DEPLOY_WORK_DIR = '/data0/www/autodeploy/' 
#更新脚本应用服务器路径
DEPLOY_REMOTE = '/data0/www/autodeploy/bin/deploy.sh'
#Tomcat脚本部署路径
TOMCAT_REMOTE = '/data0/www/autodeploy/bin/tomcat.sh' 
#SSH信息
SSH_KEY = '/home/wwwupdate/.ssh/id_rsa'
SSH_USER = 'www'
SSH_PORT = '8022'

# Redis服务器配置
REDIS_HOST = '10.71.64.132'
REDIS_PORT = 6379
REDIS_DB = 1
QUEUE_NAME = ('production', 'Tomcat')


#任务状态修改接口
TASK_STATUS_API = "http://aud.inzwc.com/api/v1.0/node_task/modify_status/"
TOMCAT_TASK_STATUS_API = "http://aud.inzwc.com/api/v1.0/tomcat_task/modify_status/"

def InitLog():
    """
    日志初始化
    """
    # 创建一个logger
    logger = logging.getLogger()
    # 创建一个handler，用于写入日志文件
    hdlr = logging.FileHandler(LOG_PATH)
    # 定义handler的输出格式
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s")
    hdlr.setFormatter(formatter)
    # 给logger添加handler
    logger.addHandler(hdlr)
    logger.setLevel(logging.NOTSET)
    return logger

class RedisQueue(object):
    """
    Redis实现一个简单队列
    """
    def __init__(self, name, namespace='queue', **redis_kwargs):
        """The default connection parameters are: host='localhost', port=6379, db=0"""
        self.__db = redis.Redis(**redis_kwargs)
        self.key = '%s:%s' %(namespace, name)

    #def __del__(self):
    #    """
    #    如果连接没有关闭, 自动关闭
    #    :return:
    #    """
    #    self.shutdown()

    def qsize(self):
        """Return the approximate size of the queue."""
        return self.__db.llen(self.key)

    def empty(self):
        """Return True if the queue is empty, False otherwise."""
        return self.qsize() == 0

    def put(self, item):
        """Put item into the queue."""
        self.__db.rpush(self.key, item)

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args block is true and timeout is None (the default), block
        if necessary until an item is available."""
        if block:
            item = self.__db.blpop(self.key, timeout=timeout)
        else:
            item = self.__db.lpop(self.key)

        if item:
            item = item[1]
        return item

    def get_nowait(self):
        """Equivalent to get(False)."""
        return self.get(False)

class TooLargeFileException(Exception):
    pass

class SSH(object):
    """
    ssh模块:提供ssh登录,远程执行命令,sftp传输文件,获取文件大小, 校验文件md5
    """
    def __init__(self, host, port=None, username=None, password=None, pkey=None, verbose=False):
        """
        :param host:
        :param port:
        :param username:
        :param password:
        :param pkey:
        :return:
        """
        self.host = host
        self.port = port if port else 8022
        self.username = username if username else 'www'
        if password and not pkey:
            self.password = password
        else:
            self.password = None
        if pkey and not password:
            self.pkey = pkey
        #ssh客户端连接
        self.client = None
        #sftp客户端连接
        self.sftp_client = None
        #实例化后就自动建立ssh连接, 同一实例共享一个ssh连接
        self.ssh_connection()
        self.transport = None
        self.sftp_open = False

    def __del__(self):
        """
        如果连接没有关闭, 自动关闭ssh连接
        :return:
        """
        self.close()
    def ssh_connection(self):
        """
        建立ssh客户端连接
        :return:
        """
        #准备建立ssh连接
        key = paramiko.RSAKey.from_private_key_file(self.pkey)
        self.client = paramiko.SSHClient()
        #设置自动接受unknown hosts
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        #建立连接
        if self.pkey:
            key = paramiko.RSAKey.from_private_key_file(self.pkey)
        self.client.connect(self.host, self.port, username=self.username, pkey=key)
        if self.password:
            pass
    def sftp_connection(self):
        """
        建立sftp客户端连接
        :return:
        """
        self.sftp_client = self.client.open_sftp()
    def get(self, src, dst):
        if not self.sftp_client:
            self.sftp_connection()
        self.sftp_client.get(src, dst)
    def put(self, src, dst):
        if not self.sftp_client:
            self.sftp_connection()
        self.sftp_client.put(src, dst)
    def cmd(self, *args):
        """
        ssh执行命令
        :param args:
        :return:
        """
        stdin, stdout, stderr = self.client.exec_command(*args)
        _out = stdout.read()
        _err = stderr.read()
        return _out, _err
    def check_path(self, path):
        """
        测试sftp
        :param path:
        :return:
        """
        try:
            self.sftp_connection()
            s = self.sftp_client.stat(path)
            print "%s's filesize is:%s" % (path, s.st_size)
        except Exception as e:
            print str(e)
    def _check_file_limit(self, path):
        """
        如果文件大小大于32768,SFTPFile.open()就会有问题
        :param path:
        :return:
        """
        info = self.sftp_client.stat(path)
        #print info.st_size
        return info.st_size > 32768
    def check_md5(self, path):
        """
        检查文件的md5
        :param path:
        :return:
        """
        file_md5 = None
        try:
            self.sftp_connection()
            #print self.sftp_client.check(path)
            if self._check_file_limit(path):
                raise TooLargeFileException()
            with self.sftp_client.open(path, 'rb') as _f:
                md5obj = hashlib.md5()
                md5obj.update(_f.read())
                file_md5 = md5obj.hexdigest()
                print "%s's md5 is:%s" % (path, file_md5)
        except Exception as e:
            print str(e)
            raise
        else:
            return file_md5
    def close(self):
        """
        关闭ssh连接
        :return:
        """
        if self.client or self.sftp_client:
            self.client.close()
        if self.sftp_open:
            self.sftp_client.close()
            self.sftp_open = False
        #self.transport.close()


class Task(object):
    """
    任务操作，包括写入参数文件、初始化工作目录、执行任务等
    """
    def __init__(self, task_dic):
        self._task_dic = task_dic
        self._deploy_local = DEPLOY_LOCAL 
        self._deploy_remote = DEPLOY_REMOTE 
        self._tomcat_local = TOMCAT_LOCAL 
        self._tomcat_remote = TOMCAT_REMOTE 
        self._ssh_key = SSH_KEY 
        self._ssh_user = SSH_USER 
        self._ssh_port = int(SSH_PORT)
        self._node_ip = self._task_dic.get('node_ip')
        self._task_no = self._task_dic.get('task_no')
        self._taskfile = TASK_PATH + self._task_no 
        self._remote_task_file = DEPLOY_WORK_DIR + '/taskfile/' + self._task_no

        #通过ssh连上服务器
        self.__ssh = SSH(host=self._node_ip, port=self._ssh_port, username=self._ssh_user, pkey=self._ssh_key)

    def write_task_file(self):
        """
        将传入的参数字典，写入一个任务更新配置文件
        """
        with open(self._taskfile, 'w') as file:
            #遍历传入的字典，将键值写入文件
            for key in self._task_dic.keys():
                arg_str = 'g_s_' + key.upper() + '="' + str(self._task_dic.get(key,'')) + '"\n'

                #去掉行尾的"/"
                if key == 'tomcat_path' and self._task_dic.get(key):
                    if self._task_dic.get(key,'')[-1] == '/':
                        arg_str = 'g_s_' + key.upper() + '="' + str(self._task_dic.get(key,''))[:-1] + '"\n'

                file.write(arg_str)

    def init_work_path(self):
        """
        初始化工作路径并上传脚本和参数文件
        """
        #创建脚本工作目录
	#print "创建脚本工作目录: %s{bin,logs,update_file_list,taskfile,tasklogs,tmp}" % DEPLOY_WORK_DIR
        self.__ssh.cmd('mkdir -p '+ DEPLOY_WORK_DIR + '/{bin,logs,update_file_list,taskfile,tasklogs,tmp}')
        #上传更新脚本
	#print "上传更新脚本,由本地%s上传到应用服务器%s" % (self._deploy_local, self._deploy_remote) 
        self.__ssh.put(self._deploy_local, self._deploy_remote)
        #上传tomcat脚本
        self.__ssh.put(self._tomcat_local, self._tomcat_remote)
        #上传更新配置文件
        self.__ssh.put(self._taskfile, self._remote_task_file)
        #将更新脚本设置为可执行权限
        self.__ssh.cmd('chmod +x ' + self._deploy_remote)
        self.__ssh.cmd('chmod +x ' + self._tomcat_remote)

    def do_deploy(self):
        """
        执行更新任务
        """
        self.__ssh.cmd('nohup ' + self._deploy_remote + ' -f ' + self._remote_task_file + '&')

    def do_tomcat(self):
        """
        执行tomcat任务
        """
        self.__ssh.cmd('nohup ' + self._tomcat_remote + ' -f ' + self._remote_task_file + '&')

        #tomcat程序打包，等待10秒后将文件取回来
        if int(self._task_dic.get('type')) == 3:
            #考虑目录路径末尾带"/"和不带的区别
            if self._task_dic.get('tomcat_path')[-1] == '/':
                package_base_path = os.path.abspath(os.path.dirname(self._task_dic.get('tomcat_path')[:-1].replace('/data0/opt/','/data0/tomcat_opt/')))
                package_file_name = os.path.basename(self._task_dic.get('tomcat_path')[:-1]) + '.tar.gz'
            else:
                package_base_path = os.path.abspath(os.path.dirname(self._task_dic.get('tomcat_path').replace('/data0/opt/','/data0/tomcat_opt/')))
                package_file_name = os.path.basename(self._task_dic.get('tomcat_path')) + '.tar.gz'

            #创建Tomcat包文件存放目录
            os.system('mkdir -p ' + package_base_path)

            #等待10s 
            time.sleep(10)
            
            attempts = 0
            success = False
            while attempts < 3 and not success:
                try:
                    #从服务器拷贝tomcat打包文件
                    self.__ssh.get(os.path.join('/tmp/',package_file_name),os.path.join(package_base_path,package_file_name))
                    success = True 
                    #拷贝完成后从服务器删除文件
                    self.__ssh.cmd('rm -f ' + os.path.join('/tmp/',package_file_name))
                except:
                    attempts += 1
                    #等待10s 
                    time.sleep(10)
                    if attempts==3:
                        break 

def task_do_thread(task):

    # 记录一条日志
    logger.info(task)
    try:    
        #更新任务实例化
        t = Task(task_dic = task)

        #从队列收到的任务字典，生成更新所需要的任务配置文件 
        logger.info('创建任务配置文件')
        t.write_task_file()

        #生成更新脚本所需要的工作目录，并上传更新脚本和任务配置文件
        logger.info('初始化应用服务器脚本工作目录')
        t.init_work_path()

        logger.info('任务发送至应用服务器')

        post_data = '{"status":1}'
        headers = {'content-type': 'application/json'}

        if task.get('queue') == 'production':
            #通过接口修改节点更新任务状态
            api_url = TASK_STATUS_API + task.get('task_no') 
            requests.post(api_url, data=post_data, headers=headers)

            #执行更新操作
            t.do_deploy()
            logger.info('执行更新任务完成')
        elif task.get('queue') == 'Tomcat':
            #通过接口修改节点更新任务状态
            api_url = TOMCAT_TASK_STATUS_API + task.get('task_no') 
            requests.post(api_url, data=post_data, headers=headers)

            #执行更新操作
            #执行Tomcat操作
            t.do_tomcat()
            logger.info('执行Tomcat任务完成')

    except Exception as e:
        print str(e)

if __name__ == '__main__':
    
    #初始化日志
    logger = InitLog()

    
    #无限循环,尝试从消息队列获得更新任务
    while True:
        for queue in QUEUE_NAME:
            #QUEUE_NAME = ('production', 'Tomcat')
            # Redis队列实例化
            q = RedisQueue(queue,host=REDIS_HOST,port=REDIS_PORT,db=REDIS_DB)

            #如果有任务消息，则执行更新，否则等待10秒重试
            if q.qsize():
                task_list = []
                threadpool = []

                #遍历获取、删除消息，添加到任务列表
                for i in range(0,q.qsize()):
                    task_list.append(json.loads(q.get()))
                    task_list[i]['queue'] = queue

                # 记录一条日志
                logger.info('从Redis队列获取%s条任务' % q.qsize())

                #for task_dic in task_list:

                jpool = Pool()
                #jpool.map(task_do_thread, task_list)
                jpool.map_async(task_do_thread, task_list)
                jpool.close()
                #jpool.join()

        #等10秒再尝试获取新任务
        time.sleep(10)
