# coding: utf-8
__author__ = 'lancger'

from datetime import datetime
from ._base import db

class App_deploy_batch(db.Model):
    """
    应用部署批次表
    """
    __tablename__ = 'app_deploy_batch'
    id = db.Column(db.Integer, primary_key = True)  #主键id，递增
    batch_no = db.Column(db.String(40), nullable=False)  #更新批次
    # app_id = db.Column(db.Integer, db.ForeignKey('apps.id'), nullable=False)  #应用id，关联apps表id字段
    app_id = db.Column(db.Integer, nullable=False)  # 应用id，关联apps表id字段
    app_name = db.Column(db.String(40), nullable=False)  #应用名，如aicai_webclient
    type = db.Column(db.Integer, nullable=False)  #更新方式：整站或增量，0 整站，1 增量
    status = db.Column(db.Integer, nullable=False)   #状态，0 审批中，1 更新中，2 更新成功，3，更新异常
    env = db.Column(db.Integer, nullable=False)   #环境：0 测试环境，1 beta环境，2 生产环境
    create_time = db.Column(db.DateTime, nullable=False)  #创建时间
    audit_time = db.Column(db.DateTime)  #审批时间
    finish_time = db.Column(db.DateTime)  #完成时间
    launcher = db.Column(db.String(20))   #发起人
    auditor = db.Column(db.String(20))    #审批人
    operator = db.Column(db.String(20))   #操作人
    is_undo = db.Column(db.Integer)     #是否回滚过，0没有，1有
    file_check = db.Column(db.Integer,default=0)     #部分更新文件检查结果,0 未检查，1检查通过，2检查不通过
    check_files_status = db.Column(db.Integer)     #是否回滚过，0文件检查成功，1文件检查异常
    message_type = db.Column(db.Integer, nullable=False)   #通知方式，0 不通知，1 邮件通知，2 短信通知，3 邮件短信均通知
    restart_tomcat = db.Column(db.Integer, nullable=False)   #是否重启tomcat，0 不重启，1 重启。
    plan = db.Column(db.Integer)     #更新安全，0，手动更新，1自动更新(审批后即进行)
    message_cc = db.Column(db.String(100))    #邮件通知抄送人
    subject = db.Column(db.String(200))  #更新主题
    after_command = db.Column(db.String(500))    #更新后执行命令
    before_command = db.Column(db.String(500))    #更新前执行命令
    desc = db.Column(db.String(600))  #更新说明
    content = db.Column(db.String(1000))  #更新内容
    business_id = db.Column(db.Integer)  #业务id,关联business表id字段

    #插入/更新记录
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

class App_deploy_node_task(db.Model):
    """
    应用部署节点任务表
    """
    __tablename__ = 'app_deploy_node_task'
    id = db.Column(db.Integer, primary_key = True)  #主键id，递增
    task_no = db.Column(db.String(40), nullable=False)  #任务号
    batch_id = db.Column(db.Integer, nullable=False)  #更新批次表id
    batch_no = db.Column(db.String(40), nullable=False)  #更新批次
    create_time = db.Column(db.DateTime, nullable=False)  #创建时间
    # node_id = db.Column(db.Integer, db.ForeignKey('app_servers.id'), nullable=False)  #服务器id
    node_id = db.Column(db.Integer, nullable=False)  # 服务器id
    node_ip = db.Column(db.String(40), nullable=False)  #部署节点
    status = db.Column(db.Integer)  #部署状态，0 排队中，1 更新中，2 异常，3成功
    finish_time = db.Column(db.DateTime)   #完成时间
    conclusion = db.Column(db.String(10))   #更新结果
    detail = db.Column(db.String(1000))    #更新详情

    #插入/更新记录
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    #删除记录
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self


class Deploy_batch_remarks(db.Model):
    """
    批次备注表
    """
    __tablename__ = 'deploy_batch_remarks'
    id = db.Column(db.Integer, primary_key = True)  #主键id，递增
    batch_id = db.Column(db.Integer, nullable=False)  #更新批次表id
    uid = db.Column(db.String(20))  #UID
    create_time = db.Column(db.DateTime, nullable=False)  #创建时间
    content = db.Column(db.String(1000))    #备注内容

    #插入/更新记录
    def save(self):
        self.create_time = datetime.now()
        db.session.add(self)
        db.session.commit()
        return self


#此表暂未用到
class App_deploy_node_info(db.Model):
    """
    节点更新信息表
    """
    __tablename__ = 'app_deploy_node_info'
    id = db.Column(db.Integer, primary_key = True)  #主键id，递增
    task_id = db.Column(db.Integer, nullable=False)  #更新历史表id
    task_no = db.Column(db.String(40), nullable=False)  #任务号
    create_time = db.Column(db.DateTime, nullable=False)  #创建时间
    logs = db.Column(db.String(2000))  #更新结果详细情况，主要是log

    #插入/更新记录
    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    #删除记录
    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

