# -*- coding:utf-8 -*-
# coding=utf-8
__author__ = 'lancger'

import ldap
import ldap.modlist as modlist
from copy import deepcopy
from flask import current_app


def DeptConvertToDn(cn=None, depart=None):
    """
    将输入的cn和部门转换为dn格式


    #输入：'中网彩\技术中心\应用开发综合部\开发一部\服务开发组'
    #输出dn:'cn=bingxin.shi,ou=服务开发组,ou=开发一部,ou=应用开发综合部,ou=技术中心,ou=中网彩,dc=aicai,dc=com'
    """

    result = depart.split('\\')
    result.reverse()
    for i in range(len(result)):
        result[i] = 'ou=' + result[i]
    delimiter = ','
    if cn is not None:
        cn_info = 'cn=' + cn + ','
        dn = cn_info + delimiter.join(result) + ',dc=aicai,dc=com'
    else:
        dn = delimiter.join(result) + ',dc=aicai,dc=com'
    return dn.decode('utf8')


def dnConvertToDept(cn=None, dn=None):
    """
    将输入的dn转换为部门格式

    如输入dn:'cn=bingxin.shi,ou=服务开发组,ou=开发一部,ou=应用开发综合部,ou=技术中心,ou=中网彩,dc=aicai,dc=com'
    输出：'中网彩\技术中心\应用开发综合部\开发一部\服务开发组'
    """
    if cn is not None:
        cn = 'cn=' + cn
        result_remove_aicaicom = dn.replace(',dc=aicai,dc=com', '').split(',ou=')
        result_remove_aicaicom.remove(cn)
    else:
        result_remove_aicaicom = dn.replace(',dc=aicai,dc=com', '').split(',ou=')
        result_remove_aicaicom[0] = result_remove_aicaicom[0].replace('ou=', '')

    result_remove_aicaicom.reverse()
    delimiter = '\\'
    result = delimiter.join(result_remove_aicaicom)
    return result.decode('utf8')

def openldap_conn_open():
    """
    建立ldap连接
    """

    config = current_app.config

    # 实例化utils.ldapHandle，连接好ldap，并准备好接受查询
    openldap_conn = openldapHandle(server_uri=config.get('LDAP_SERVER_URI'),
                                   base_dn=config.get('LDAP_BASE_DN'),
                                   username=config.get('LDAP_LOGIN_USER'),
                                   password=config.get('LDAP_LOGIN_PASSWD'))
    print config.get('LDAP_LOGIN_USER')
    print config.get('LDAP_LOGIN_PASSWD')

    return openldap_conn


def ad_conn_open():
    """
    建立ldap连接
    """

    config = current_app.config

    # 实例化utils.ldapHandle，连接好ldap，并准备好接受查询
    ad_conn = adHandle(server_uri=config.get('AD_SERVER_URI'),
                       base_dn=config.get('AD_BASE_DN'),
                       username=config.get('AD_LOGIN_USER'),
                       password=config.get('AD_LOGIN_PASSWD'))

    return ad_conn


class adHandle:
    """ AD操作"""

    def __init__(self, server_uri=None, base_dn=None, username=None, password=None):
        self.server_uri = server_uri
        self.base_dn = base_dn
        self.username = username
        self.password = password

        ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

        try:
            self.ldapconn = ldap.initialize(self.server_uri)
            self.ldapconn.set_option(ldap.OPT_TIMEOUT, 10)
            self.ldapconn.simple_bind_s(self.username, self.password)
            self.ldapconn.set_option(ldap.OPT_REFERRALS, 0)
            self.ldapconn.set_option(ldap.OPT_X_TLS, ldap.OPT_X_TLS_DEMAND)
            # self.ldapconn.set_option(ldap.OPT_X_TLS_CACERTFILE, os.getcwd() + "/app/utils/certnew.cer")
            #print os.getcwd() + "/app/utils/certnew.cer"
            self.ldapconn.set_option(ldap.OPT_X_TLS_DEMAND, True)
            self.ldapconn.set_option(ldap.OPT_DEBUG_LEVEL, 255)
        except ldap.LDAPError, e:
            print e

        self.ldapconn.protocal_version = ldap.VERSION3

    def ad_search_dn(self, account=None):
        """
        根据用户名返回dn


        一条dn就相当于数据库里的一条记录。
        在ldap里类似cn=username,ou=users,dc=gccmx,dc=cn,验证用户密码，必须先检索出该DN
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = None
        searchFilter = "cn=" + account

        try:
            ldap_result_id = obj.search(self.base_dn, searchScope, searchFilter, retrieveAttributes)
            result_type, result_data = obj.result(ldap_result_id, 0)
            # 返回数据格式
            # ('cn=django,ou=users,dc=gccmx,dc=cn',
            #    {  'objectClass': ['inetOrgPerson', 'top'],
            #        'userPassword': ['{MD5}lueSGJZetyySpUndWjMBEg=='],
            #        'cn': ['django'], 'sn': ['django']  }  )
            #
            if result_type == ldap.RES_SEARCH_ENTRY:
                #dn = result[0][0]
                return result_data[0][0]
            else:
                return None
        except ldap.LDAPError, e:
            print e
            return False

    def ad_get_all_user(self, search_base_dn=None):
        """
        检索base_dn，返回所有用户信息

        获取所有用户和属性数据，返回一个列表字典嵌套数据结构
        """

        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['cn',
                              'dn',
                              'sAMAccountName',
                              'distinguishedName',
                              'displayName',
                              'memberOf',
                              'sn',
                              'userPrincipalName',
                              'description',
                              'objectGUID']
        searchFilter = '(&(displayName=*)(!(cn=ZWC*)))'

        base_dn = search_base_dn

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            # 返回一个列表字典嵌套数据结构
            result = []

            for item in search_result:
                data = {}
                data['dn'] = item[0]
                for key, value in item[1].iteritems():
                    # objectClass是一个列表,仍保存为一个列表
                    if key == 'objectClass':
                        data[key] = value
                    else:
                        data[key] = value[0]

                result.append(data)

            return result

        except ldap.LDAPError, e:
            print e
            return False

    def ad_get_all_ou(self, search_base_dn=None):
        """
        检索base_dn，返回所有组织信息

        根据传入的search_base_dn，获取所有组织单元
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['dn',
                              'objectClass',
                              'ou',
                              'objectGUID']

        # 过滤要排队OU=PC/win7/win8
        searchFilter = "(&(&(ou=*)(!(ou=PC)))(!(ou=win*)))"
        base_dn = search_base_dn

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            #返回一个列表字典嵌套数据结构
            result = []

            for item in search_result:
                data = {}
                data['dn'] = item[0]
                #不要返回本身
                if item[0] == 'OU=中网彩,DC=aicai,DC=com' or item[0] != search_base_dn:
                    for key, value in item[1].iteritems():
                        data[key] = value[0]
                        #objectClass是一个列表,仍保存为一个列表
                        if key == 'objectClass':
                            data[key] = value
                    result.append(data)

            return result

        except ldap.LDAPError, e:
            print e
            return False

    def ad_get_ou_all_dn(self, dn=None):
        """
        获取一个dn下的所有dn,包括user和ou
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['dn']
        # 过滤要排队OU=PC/win7/win8
        searchFilter = "(&(&(|(cn=*)(ou=*))(!(ou=PC)))(!(ou=win*)))"
        base_dn = dn

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            #返回一个列表字典嵌套数据结构
            result = []

            for item in search_result:
                data = {}
                if item[0] != dn:
                    data['dn'] = item[0]
                    for key, value in item[1].iteritems():
                        data[key] = value[0]
                    result.append(data)

            return result

        except ldap.LDAPError, e:
            print e
            return False

    def ad_get_ou_onelevel_dn(self, dn=None):
        """
        获取一个ou下一层的所有dn
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_ONELEVEL
        retrieveAttributes = ['dn',
                              'displayName']
        searchFilter = "(|(cn=*)(ou=*))"
        base_dn = dn

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            # 返回一个列表字典嵌套数据结构
            result = []

            for item in search_result:
                data = {}
                data['dn'] = item[0]
                for key, value in item[1].iteritems():
                    data[key] = value[0]
                result.append(data)

            return result

        except ldap.LDAPError, e:
            print e
            return False

    def ad_get_a_ou(self, dn=None):
        """
        根据传入的dn，获取一个组织单元
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['dn',
                              'objectClass',
                              'ou',
                              'objectGUID']
        searchFilter = "ou=*"
        base_dn = dn

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            # 返回一个列表字典嵌套数据结构
            result = []

            for item in search_result:
                data = {}
                data['dn'] = item[0]
                for key, value in item[1].iteritems():
                    data[key] = value[0]
                    #objectClass是一个列表,仍保存为一个列表
                    if key == 'objectClass':
                        data[key] = value
                result.append(data)

            return result

        except ldap.LDAPError, e:
            print e
            return False

    def ad_get_a_user(self, search_cn=None, search_dn=None):
        """
        获取一个用户的属性
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['cn',
                              'dn',
                              'sAMAccountName',
                              'distinguishedName',
                              'displayName',
                              'memberOf',
                              'sn',
                              'userPrincipalName',
                              'description',
                              'objectGUID']

        if search_dn and search_cn is None:
            base_dn = search_dn
            searchFilter = "cn=*"
        elif search_cn and search_dn is None:
            base_dn = self.base_dn
            searchFilter = "cn=%s" % search_cn
        else:
            return False

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            return search_result
        except ldap.LDAPError, e:
            print e
            return False

    def ad_add_user(self, dn=None, name=None):
        """
        新增一个用户
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        NORMAL_ACCOUNT = 512
        DONT_EXPIRE_PASSWORD = 65536

        password = 'zwc123!@#'
        unicode_pass = unicode('\"' + password + '\"', 'iso-8859-1')
        password_value = unicode_pass.encode('utf-16-le')

        attrs = {}
        # 通过dn获取帐号名
        account = dn.split(',')[0].split('=')[-1].encode('utf-8')
        attrs['displayName'] = [name.encode('utf-8')]
        attrs['cn'] = [account]
        attrs['sAMAccountName'] = [account]
        attrs['objectClass'] = ['top', 'person', 'organizationalPerson', 'user']
        attrs['userPrincipalName'] = [str(account + '@' + '.'.join(dn.lower().split(',dc=')[-2:]))]  #根据dn生成@aicai.com邮箱后缀
        attrs['unicodePwd'] = [password_value]  #用户登录密码
        attrs['userAccountControl'] = str(NORMAL_ACCOUNT + DONT_EXPIRE_PASSWORD)

        ldif = modlist.addModlist(attrs)

        try:
            obj.add_s(dn, ldif)
            return True
        except ldap.ALREADY_EXISTS:
            print '用户已经存在'
            return False
        except ldap.LDAPError, e:
            print e
            return False

    def ad_user_reset_password(self, dn=None, newpass=None):
        """
        修改用户密码
        """

        obj = self.ldapconn

        unicode_pass = unicode('\"' + newpass + '\"', 'iso-8859-1')
        password_value = unicode_pass.encode('utf-16-le')
        add_pass = [(ldap.MOD_REPLACE, 'unicodePwd', [password_value])]

        try:
            obj.modify_s(dn, add_pass)
            return True
        except Exception, e:
            print e
            return False

    def ad_add_ou(self, dn=None):
        """
        增加一个组(OU)
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        attrs = {}
        attrs['ou'] = [dn.lower().replace('ou=', '').split(',')[0].encode('utf-8')]
        attrs['objectClass'] = ['organizationalUnit', 'top']

        ldif = modlist.addModlist(attrs)

        try:
            obj.add_s(dn, ldif)
            return True
        except ldap.ALREADY_EXISTS:
            print 'already exists %s' % dn
            return False
        except ldap.LDAPError, e:
            print e
            return False

    def ad_del_dn(self, dn=None):
        """
        删除一个用户或组

        删除组织，确保组织下没有用户
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        try:
            obj.delete_s(dn)
            return True
        except ldap.NO_SUCH_OBJECT, e:
            print e
            return False

    def ad_user_change_ou(self, dn=None, newou=None):
        """
        用户变更部门
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        # 通过dn获取cn字段如'cn=xuki.xu'
        cn = dn.split(',')[0]

        try:
            obj.rename_s(dn, cn, newou)
            return True
        except ldap.NO_SUCH_OBJECT, e:
            print e
            return False

    def ad_conn_close(self):
        """
        ad连接关闭
        """
        obj = self.ldapconn
        obj.unbind()


class openldapHandle:
    """ openldap操作"""

    def __init__(self, server_uri=None, base_dn=None, username=None, password=None):
        self.server_uri = server_uri
        self.base_dn = base_dn
        self.username = username
        self.password = password
        try:
            self.ldapconn = ldap.initialize(self.server_uri)
            self.ldapconn.set_option(ldap.OPT_TIMEOUT, 10)
            self.ldapconn.simple_bind_s(self.username, self.password)
        except ldap.LDAPError, e:
            print e

    # 根据表单提交的用户名，检索该用户的dn,一条dn就相当于数据库里的一条记录。
    #在ldap里类似cn=username,ou=users,dc=gccmx,dc=cn,验证用户密码，必须先检索出该DN
    def ldap_search_dn(self, uid=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = None
        searchFilter = "cn=" + uid

        try:
            ldap_result_id = obj.search(self.base_dn, searchScope, searchFilter, retrieveAttributes)
            result_type, result_data = obj.result(ldap_result_id, 0)
            #返回数据格式
            #('cn=django,ou=users,dc=gccmx,dc=cn',
            #    {  'objectClass': ['inetOrgPerson', 'top'],
            #        'userPassword': ['{MD5}lueSGJZetyySpUndWjMBEg=='],
            #        'cn': ['django'], 'sn': ['django']  }  )
            #
            if result_type == ldap.RES_SEARCH_ENTRY:
                #dn = result[0][0]
                return result_data[0][0]
            else:
                return None
        except ldap.LDAPError, e:
            print e
            return False

    #根据传入的search_base_dn，获取所有用户和属性数据，返回一个列表字典嵌套数据结构
    def ldap_get_all_user(self, search_base_dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['cn',
                              'sn',
                              'uid',
                              'dn',
                              'mobile',
                              'uidNumber',
                              'ipHostNumber',
                              'loginShell',
                              'mail',
                              'gidNumber',
                              'homeDirectory',
                              'objectClass',
                              'userPassword',
                              'givenname',
                              'pager',
                              'uniqueMember']
        if search_base_dn == 'ou=groups,dc=aicai,dc=com':
            searchFilter = 'cn=*'
        else:
            searchFilter = 'mail=*@aicai.com'

        base_dn = search_base_dn

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            #返回一个列表字典嵌套数据结构
            result = []

            for item in search_result:
                data = {}
                data['dn'] = item[0]
                for key, value in item[1].iteritems():
                    #objectClass是一个列表,仍保存为一个列表
                    if key == 'objectClass':
                        data[key] = value
                    elif key == 'pager':
                        data[key] = value
                    elif key == 'uniqueMember':
                        data[key] = value
                    else:
                        data[key] = value[0]
                result.append(data)

            return result

        except ldap.LDAPError, e:
            print e
            return False

    #根据传入的search_base_dn，获取所有组织单元
    def ldap_get_all_ou(self, search_base_dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['dn',
                              'objectClass',
                              'ou']
        searchFilter = "ou=*"
        base_dn = search_base_dn

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            #返回一个列表字典嵌套数据结构
            result = []

            for item in search_result:
                data = {}
                data['dn'] = item[0]
                for key, value in item[1].iteritems():
                    data[key] = value[0]
                    #objectClass是一个列表,仍保存为一个列表
                    if key == 'objectClass':
                        data[key] = value
                result.append(data)

            return result

        except ldap.LDAPError, e:
            print e
            return False

    def ldap_get_ou_onelevel_dn(self, dn=None):
        """
        获取一个ou下一层的所有dn
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_ONELEVEL
        retrieveAttributes = ['dn',
                              'ou',
                              'sn']
        searchFilter = "(|(cn=*)(ou=*))"
        base_dn = dn

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            # 返回一个列表字典嵌套数据结构
            result = []

            for item in search_result:
                data = {}
                data['dn'] = item[0]
                for key, value in item[1].iteritems():
                    data[key] = value[0]
                result.append(data)

            return result

        except ldap.LDAPError, e:
            print e
            return False

    #根据传入的dn，获取一个组织单元
    def ldap_get_a_ou(self, dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['dn',
                              'objectClass',
                              'ou']
        searchFilter = "ou=*"

        try:
            search_result = obj.search_s(dn, searchScope, searchFilter, retrieveAttributes)
            #返回一个列表字典嵌套数据结构
            result = []

            for item in search_result:
                data = {}
                data['dn'] = item[0]
                for key, value in item[1].iteritems():
                    data[key] = value[0]
                    #objectClass是一个列表,仍保存为一个列表
                    if key == 'objectClass':
                        data[key] = value
                result.append(data)

            return result

        except ldap.LDAPError, e:
            print e
            return False

    #获取一个用户的属性
    def ldap_get_a_user(self, search_cn=None, search_dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['cn',
                              'sn',
                              'uid',
                              'dn',
                              'mobile',
                              'uidNumber',
                              'ipHostNumber',
                              'loginShell',
                              'mail',
                              'gidNumber',
                              'homeDirectory',
                              'objectClass',
                              'userPassword',
                              'givenname',
                              'pager']

        if search_dn and search_cn is None:
            base_dn = search_dn
            searchFilter = "cn=*"
        elif search_cn and search_dn is None:
            base_dn = self.base_dn
            searchFilter = "cn=%s" % search_cn
        else:
            return False

        try:
            search_result = obj.search_s(base_dn, searchScope, searchFilter, retrieveAttributes)
            #返回一个列表，列表包含2个元素，[0]为dn,[1]为一个属性字典，格式如下
            #[('cn=xuki.xu,ou=\xe7\xb3\xbb\xe7\xbb\x9f\xe8\xbf\x90\xe7\xbb\xb4\xe9\x83\xa8,ou=\xe6\x8a\x80\xe6\x9c\xaf\xe4\xb8\xad\xe5\xbf\x83,ou=\xe4\xb8\xad\xe7\xbd\x91\xe5\xbd\xa9,dc=aicai,dc=com',
            #  {'cn': ['xuki.xu'],
            #   'gidNumber': ['2000'],
            #   'givenName': ['xu'],
            #   'homeDirectory': ['/home/xuki.xu'],
            #   'ipHostNumber': ['2.0.1.10'],
            #   'loginShell': ['/usr/local/bin/secshell'],
            #   'mail': ['xuki.xu@aicai.com'],
            #   'mobile': ['13510481271'],
            #   'objectClass': ['inetOrgPerson', 'posixAccount', 'top', 'ipHost'],
            #   'sn': ['\xe8\xae\xb8\xe9\x9d\x96'],
            #   'uid': ['xuki.xu'],
            #   'uidNumber': ['1000'],
            #   'userPassword': ['{SSHA}jcSAV2ke6ye3CMVKoaG30n+xuOPY8+cWkG']})]

            return search_result
        except ldap.LDAPError, e:
            print e
            return False

    #新增一个用户
    def ldap_add_user(self, dn=None, sn=None, mobile=None, uidnumber=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        attrs = {}
        cn = dn.split(',')[0].split('=')[-1].encode('utf-8')
        attrs['cn'] = [cn]
        attrs['sn'] = [sn.encode('utf-8')]
        attrs['mobile'] = [mobile.encode('utf-8')]
        attrs['mail'] = [cn + '@aicai.com']
        attrs['givenname'] = [cn.split('.')[-1]]
        attrs['uid'] = [cn]
        attrs['uidNumber'] = [str(uidnumber)]
        attrs['loginShell'] = ['/sbin/false']
        attrs['homeDirectory'] = ['/home/null']
        attrs['objectClass'] = ['top', 'posixAccount', 'ipHost', 'inetOrgPerson']
        attrs['gidNumber'] = ['2000']
        attrs['ipHostNumber'] = ['1.1.1.1']
        attrs['userPassword'] = ['{SSHA}b14XtgW07oqEPJ+MgekrFGk9ztG8qqZa']
        print attrs
        print dn

        ldif = modlist.addModlist(attrs)

        try:
            obj.add_s(dn, ldif)
            return True
        except ldap.ALREADY_EXISTS:
            print '用户已经存在'
            return False
        except ldap.LDAPError, e:
            print e
            return False

    #新增一个用户权限组
    def ldap_add_perm_group(self, dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        attrs = {}
        cn = dn.split(',')[0].split('=')[-1].encode('utf-8')
        attrs['cn'] = [cn]
        attrs['objectClass'] = ['top', 'groupOfUniqueNames']
        attrs['uniqueMember'] = ['']

        ldif = modlist.addModlist(attrs)

        try:
            obj.add_s(dn, ldif)
            return True
        except ldap.ALREADY_EXISTS:
            print '权限组已经存在'
            return False
        except ldap.LDAPError, e:
            print e
            return False


    #删除一个用户
    def ldap_delete_user(self, delete_dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        try:
            obj.delete_s(delete_dn)
            return True
        except ldap.NO_SUCH_OBJECT, e:
            print e
            return False

    #用户验证，根据传递来的用户名和密码，搜索LDAP，返回boolean值
    def ldap_user_auth(self, uid=None, passwd=None):
        obj = self.ldapconn

        target_cn = self.ldap_search_dn(uid=uid)
        try:
            if obj.simple_bind_s(target_cn, passwd):
                return True
            else:
                return False
        except ldap.LDAPError, e:
            print e
            return False

    #编辑一个用户属性
    def ldap_modify_user(self, modify_dn=None, change_ldif_dict=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        #要获取当前用户的属性
        now_ldif_dict = self.ldap_get_a_user(search_dn=modify_dn)[0][1]

        new_ldif_dict = {}
        old_ldif_dict = {}

        for _key, _value in change_ldif_dict.items():
            if now_ldif_dict.has_key(_key):
                old_ldif_dict[_key] = now_ldif_dict[_key]
                new_ldif_dict[_key] = _value

        try:
            ldif = modlist.modifyModlist(old_ldif_dict, new_ldif_dict)
            if obj.modify_s(modify_dn, ldif):
                #print '修改成功:%s' % ldif
                return True
            else:
                return False

        except Exception, e:
            print e
            return False

    #增加一个用户属性
    def _ldap_add_user_attr(self, modify_dn=None, add_attr_list=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        try:
            if obj.modify_s(modify_dn, add_attr_list):
                print '属性添加成功'
                return True
            else:
                return False

        except Exception, e:
            print e
            return False

    #增加用户pager属性
    def ldap_add_user_attr_pager(self, modify_dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        add_attr_list = [
            (ldap.MOD_ADD, 'pager', ['1.1.1.1/3306:1.1.1.1:3306'])
        ]

        try:
            if self._ldap_add_user_attr(modify_dn=modify_dn, add_attr_list=add_attr_list):
                #print 'pager属性添加成功'
                return True
            else:
                return False

        except Exception, e:
            print e
            return False


    #移动用户，一般是变更部门
    def ldap_move_user(self, dn=None, uid=None, new_ou=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        uid_cn = 'cn=%s' % uid

        try:
            if obj.rename_s(dn, uid_cn, new_ou):
                #print '用户部门修改成功'
                return True
            else:
                return False

        except Exception, e:
            print e
            return False


    #修改用户密码
    def ldap_user_change_password(self, dn=None, oldpass=None, newpass=None):

        obj = self.ldapconn
        try:
            if obj.passwd_s(dn, oldpass, newpass):
                return True
            else:
                return False
        except Exception, e:
            print e
            return False

    #增加一个组
    def ldap_add_group(self, dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        attrs = {}
        attrs['ou'] = [dn.replace('ou=', '').split(',')[0].encode('utf-8')]
        attrs['objectClass'] = ['organizationalUnit', 'top']
        print attrs
        print dn

        ldif = modlist.addModlist(attrs)

        try:
            obj.add_s(dn, ldif)
            return True
        except ldap.ALREADY_EXISTS:
            print 'already exists %s' % dn
            return False
        except ldap.LDAPError, e:
            print e
            return False

    #重命名一个组
    def ldap_rename_group(self, old_dn=None, new_dn=None):
        pass

    #关闭ldap连接
    def ldap_conn_close(self):
        obj = self.ldapconn
        obj.unbind()

    #jira/wiki权限配置，增加一个用户到配置项下
    def ldap_add_user_to_pm(self, pm_dn=None, user_dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        #要获取当前用户的属性
        old_ldif_dict = self.ldap_pm_get_attrs(pm_dn=pm_dn)

        new_ldif_dict = deepcopy(old_ldif_dict)
        #print '调试信息user_dn:%s' % user_dn
        new_ldif_dict['uniqueMember'].append(user_dn.encode('utf8'))
        #print '调试信息new_ldif_dict:%s' % new_ldif_dict

        try:
            ldif = modlist.modifyModlist(old_ldif_dict, new_ldif_dict)
            if obj.modify_s(pm_dn, ldif):
                #print '修改成功:%s' % ldif
                return True
            else:
                return False

        except Exception, e:
            print e
            return False

    #jira/wiki权限配置，删除一个配置项下的用户
    def ldap_del_user_from_pm(self, pm_dn=None, user_dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        #要获取当前用户的属性
        old_ldif_dict = self.ldap_pm_get_attrs(pm_dn=pm_dn)

        new_ldif_dict = deepcopy(old_ldif_dict)

        new_ldif_dict['uniqueMember'].remove(user_dn.encode('utf8'))

        try:
            ldif = modlist.modifyModlist(old_ldif_dict, new_ldif_dict)
            if obj.modify_s(pm_dn, ldif):
                #print '修改成功:%s' % ldif
                return True
            else:
                return False

        except Exception, e:
            print e
            return False

    #jira/wiki权限配置，配置项是否包含一个用户,包含则返回True
    def ldap_pm_has_user(self, pm_dn=None, user_dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['dn',
                              'uniqueMember']

        searchFilter = 'uniqueMember=%s' % user_dn

        try:
            search_result = obj.search_s(pm_dn, searchScope, searchFilter, retrieveAttributes)
            if len(search_result):
                return True
            else:
                return False
        except ldap.LDAPError, e:
            print e
            return False

    #jira/wiki权限配置，获取配置项权限配置
    def ldap_pm_get_attrs(self, pm_dn=None):
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['dn',
                              'uniqueMember']

        searchFilter = 'cn=*'

        try:
            search_result = obj.search_s(pm_dn, searchScope, searchFilter, retrieveAttributes)
            if len(search_result):
                return search_result[0][1]
            else:
                return False
        except ldap.LDAPError, e:
            print e
            return False

    def ldap_user_change_ou(self, dn=None, newou=None):
        """
        用户变更部门
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        #通过dn获取cn字段如'cn=xuki.xu'
        cn = dn.split(',')[0]

        try:
            obj.rename_s(dn, cn, newou)
            return True
        except ldap.NO_SUCH_OBJECT, e:
            print e
            return False

    def ldap_del_dn(self, dn=None):
        """
        删除一个用户或组

        删除组织，确保组织下没有用户
        """
        obj = self.ldapconn
        obj.protocal_version = ldap.VERSION3

        try:
            obj.delete_s(dn)
            return True
        except ldap.NO_SUCH_OBJECT, e:
            print e
            return False




