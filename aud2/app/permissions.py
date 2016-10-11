# -*- coding:utf-8 -*-
#coding=utf-8
__author__ = 'lancger'

from permission import Permission
from rules import UserRule, AdminRule, DeveloperRule, AuditorRule, SARule

class UserPermission(Permission):
    def rule(self):
        return UserRule()

class DeveloperPermission(Permission):
    def rule(self):
        return DeveloperRule() | AuditorRule()

class AuditorPermission(Permission):
    def rule(self):
        return AuditorRule() | AdminRule()

class SAPermission(Permission):
    def rule(self):
        return SARule() | AdminRule()

class AdminPermission(Permission):
    def rule(self):
        return AdminRule()