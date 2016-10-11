# coding: utf-8
__author__ = 'xujing'

import os

BASE_DIR = os.path.abspath('./')


class Config(object):
    """配置基类"""
    # Flask app config

    # Root path of project
    PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    CSRF_ENABLED = True
    # WTF_CSRF_CHECK_DEFAULT = False
    SECRET_KEY = 'helloword'

    POSTS_PER_PAGE = 10

    #全局关闭crsf,接口调试
    WTF_CSRF_ENABLED = False

    # 数据库连接配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:zwc123@192.168.66.93/aud?charset=utf8'
    # SQLALCHEMY_DATABASE_URI = 'mysql://root:zwc123@localhost/aud2?charset=utf8'
    SQLALCHEMY_MIGRATE_REPO = os.path.join(BASE_DIR, 'db_repository')
    SQLALCHEMY_RECORD_QUERIES = False
    # slow database query threshold (in seconds)
    DATABASE_QUERY_TIMEOUT = 0.2
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    #该系统所运行域名
    DOMAIN_NAME = 'ums.inzwc.com'

    #邮件服务器配置
    MAIL_SERVER = 'mail.aicai.com'
    MAIL_USERNAME = 'aud@aicai.com'
    MAIL_PASSWORD = 'C8phgN9VYhbt'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_DEFAULT_SENDER = 'aud@aicai.com'

    DEBUG_LOG = 'logs/debug.log'
    ERROR_LOG = 'logs/error.log'

    LDAP_SEARCH_BASE = 'ou=中网彩,dc=aicai,dc=com'

    #LDAP服务器配置
    LDAP_SERVER_URI = 'ldap://192.168.90.159:389'
    LDAP_BASE_DN = 'dc=aicai,dc=com'
    LDAP_LOGIN_USER = 'cn=aicaiadmin,ou=authusers,dc=aicai,dc=com'
    LDAP_LOGIN_PASSWD = 'Yae0zohV2mieJooCho'


    #短信验证码设置
    SMS_URL = 'http://sms.aicai.inzwc.com/syncSendSms.jhtml'
    SMS_CODE_LENGTH = 6
    SMS_VCODE_MES = u"亲，您本次操作的验证码为：%s"
    SMS_PASSWD_EXPIRE_MES = u"%s，您在新浪爱彩内部帐号密码将在%s过期，请及时通过内网访问帐号自助系统修改密码！系统运维部-帐号管理中心 %s"



    #更新及流程相关字典
    DEPLOY_STATUS = ('审批中','审核驳回', '待更新', '更新中', '更新成功', '更新异常', '取消更新')
    ADD_DEPLOY_TYPE = ('整站更新', '增量更新')
    DEPLOY_TYPE = ('整站更新', '增量更新', '全站回滚', '增量回滚')
    MESSAGE_TYPE = ('不通知', '邮件通知', '短信通知', '邮件短信均通知')
    NODE_TASK_STATUS = ('排队中', '更新中', '更新异常', '更新成功')
    DEPLOY_PLAN = ('手动更新', '自动更新(审批后即进行)')


    #一些运行环境
    # BETA_SERVER = ('192.168.91.40','10.71.64.226')
    RSYNC_USER = 'www'
    RSYNC = '/usr/bin/rsync'
    RSYNC_TEST_OPTIONS = ' -avzKIr -n '
    #上传文件测试脚本
    UPDATE_FILE_LIST_CHECK_SCRIPT = os.path.join(BASE_DIR,'scripts/check_update_file.sh')
    #项目部署服务器同nginx upstream检测脚本
    APP_UPSTREAM_CHECK_SCRIPT = os.path.join(BASE_DIR,'scripts/app_upstream_check.py')
    #项目部署服务器IP端口检测脚本
    APP_REAL_SERVER_CHECK_SCRIPT = os.path.join(BASE_DIR,'scripts/app_real_server_check.py')


    #系统运行基目录
    WWW_BASE_DIR = '/data0/www/aud.inzwc.com/'
    #更新文件列表存放路径
    UPDATE_FILE_LIST = os.path.join(WWW_BASE_DIR, 'filelist')
    #上传文件临时存放路径
    UPDATE_FILE_TEST_PATH = '/tmp/update_test_path'
    #任务日志上传存放路径
    TASK_LOG_BASE_URL = os.path.join(WWW_BASE_DIR, 'tasklogs')
    #tomcat日志上传存放路径
    TOMCAT_LOG_BASE_URL = os.path.join(WWW_BASE_DIR, 'tomcatlogs')


    ###字典
    # 服务器相关字典
    SERVER_LOCATION = ('松日', '广州七星岗电信', '广州沙溪电信', '北京北显联通', '深圳龙岗电信', '阿里云杭州')
    SERVER_TYPE = ('物理服务器', 'KVM虚拟机', 'LXC虚拟机', 'Hyper-v虚拟机', 'openvz容器', 'vmware', "其它")
    APP_ENV = ('测试环境(Daily)', '测试环境(Project)', 'Beta环境', '生产环境')
    SERVER_STATUS = ('服务器准备中', '正常运行中', '维护中', '已下架', '已报废')

    #业务类型相关字典
    BUSSINESS_TYPE = ('保留', '彩票业务', '滴滴业务', '港股行情', '港股交易', '金融业务')

    #项目配置相关字典
   # APP_SITE_TYPE = ('爱彩前端', '爱彩后端', '爱彩后台', '滴滴前端', '滴滴后端', '滴滴后台', '港股行情前端', '港股行情后端', '港股行情后台', '港股交易前端', '港股交易后端', '港股交易后端'） 
    APP_SITE_TYPE = ('爱彩前端', '爱彩后端', '爱彩后台', '滴滴前端', '滴滴后端', '滴滴后台', '港股行情前端', '港股行情后端', '股行情后台', '港股交易前端', '港股交易后端', '港股交易后端','爱刮刮前端', '爱刮刮后端', '爱刮刮后端')
    RSYNC_PATH_NAME = ('www','res')


    #nginx UpStream接口
    #查询应用服务器部署接口
    WAF_UPSTREAM_GET_APP_SERVER_API = 'http://waf.2caipiao.com/upstream/get?mode=all&appname='
    #删除upstream server接口
    WAF_UPSTREAM_DEL_APP_SERVER_API = 'http://waf.2caipiao.com/upstream/set?mode=del&appname='
    #添加upstream server接口
    WAF_UPSTREAM_ADD_APP_SERVER_API = 'http://waf.2caipiao.com/upstream/set?mode=add&appname='

    #WAF设置接口
    WAF_UPSTREAM_SET_RAM_API = 'http://waf.2caipiao.com/upstream/jsonset'
    WAF_UPSTREAM_SET_FILE_API = 'http://waf.2caipiao.com/upstream/jsonfile'

    API_STATUS = ('成功', '失败')

    #cmdb服务器状态和配置信息查询接口
    #单台查询接口
    CMDB_GET_ONE_SERVER_API = 'http://cmdb.inzwc.com/api/v1.0/server/list_conf/'
    #多台查询接口
    CMDB_GET_SOME_SERVER_API = 'http://cmdb.inzwc.com/'
    #全部查询接口
    CMDB_GET_ALL_SERVER_API = 'http://cmdb.inzwc.com/api/v1.0/all/server/list'


     #tomcat任务相关字典
    TOMCAT_OPERATION_TYPE = ('部署', '移除', '重启', 'Tomcat打包', 'APP目录打包', 'APP部署', '同时部署APP和Tomcat', '停止tomcat')
    TOMCAT_OPERATION_STATUS = ('排队中', '操作中', '操作异常', '操作成功')

    #重启及流程相关字典
    TOMCAT_RESTART_STATUS = ('审批中', '审核驳回', '待重启', '重启中', '重启成功', '重启异常', '取消重启')
    RESTART_NODETASK_STATUS = ('排队中', '重启中', '重启异常', '重启成功')
    # NODE_TASK_STATUS = ('排队中', '更新中', '更新异常', '更新成功')
    # TOMCAT_RESTART_STATUS = ('审批中', '审批通过', '审核驳回', '待重启', '重启中', '重启成功', '重启异常', '取消重启')



    #用户角色相关字典
    USER_ROLES = ('保留', '普通用户', '开发人员', '审批人', '运维人员', '管理员')
    USER_ROLES_TAG = ('None', 'is_user', 'is_developer', 'is_auditor', 'is_sa', 'is_admin')
    CHECK_UPDATEFILES_STATUS = ('文件检查成功', '文件检查有异常')

    #消息通知字典
    MESSAGE_LOG_TYPE = ('站内通知', '邮件', '短信', '微信')

    #用户操作审计相关字典
    USER_ACTION_CONVERT = {
        'adddeploy': '发起更新',
        'rollback': '回滚',
        'login': '登录',
        'logout': '登出',
        'ldapsync': 'LDAP同步',
        'editrole': '编辑角色',
        'addserver': '增加服务器',
        'editserver': '编辑服务器',
        'addsite': '增加站点类别',
        'editsite': '编辑站点类别',
        'addapp': '增加项目',
        'editapp': '编辑项目',
        'delappnode': '删除项目节点',
        'tomcat_task': '添加Tomcat任务',
        'approve_success': '审批通过',
        'approve_notgo': '审批驳回',
        'dodeploy': '操作更新',
        'addappnode': '添加项目节点',
        'editdeploy': '编辑更新',
        'notgo': '取消更新',
        'tomcat_reboot': 'Tomcat重启',
        'do_tomcat_restart': '执行重启'
    }

    # web根路径
    WEB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # SSL证书路径
    SSL_KEY = os.path.join(WEB_ROOT, 'cert/ssl/aud2.inzwc.com.key')
    SSL_CRT = os.path.join(WEB_ROOT, 'cert/ssl/aud2.inzwc.com.crt')

    # 签名验签证书路径
    PRI_KEY_PATH = os.path.join(WEB_ROOT, 'cert/pri/aud2.inzwc.com.pem')
    PUB_KEY_DIR = os.path.join(WEB_ROOT, 'cert/pub')
