# -*- coding:utf-8 -*-
#coding=utf-8
__author__ = 'lancger'

# coding: utf-8
from flask import g, redirect, url_for, abort, flash
from permission import Rule


class UserRule(Rule):
    def check(self):
        return g.user

    def deny(self):
        abort(403)


class DeveloperRule(Rule):
    def base(self):
        return UserRule()

    def check(self):
        return g.user.is_developer()

    def deny(self):
        abort(403)

class AuditorRule(Rule):
    def base(self):
        return UserRule()

    def check(self):
        return g.user.is_auditor()

    def deny(self):
        abort(403)

class SARule(Rule):
    def base(self):
        return UserRule()

    def check(self):
        return g.user.is_sa()

    def deny(self):
        abort(403)

class AdminRule(Rule):
    def base(self):
        return UserRule()

    def check(self):
        return g.user.is_admin()

    def deny(self):
        abort(403)