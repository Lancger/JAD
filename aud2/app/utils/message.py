# -*- coding:utf-8 -*-
#coding=utf-8
__author__ = 'lancger'

from flask import render_template, redirect, request, url_for, copy_current_request_context, current_app
from app.mails import mail
# from app import mails
from flask.ext.mail import Message
import app.models
from datetime import datetime,date,timedelta
from threading import Thread

#消息发送
class Mess(object):
    """
    消息发送，根据传入的参数，发送内站通知，邮件通知，短信或微信通知
    """
    def __init__(self, receiver_list=None, mes_content=None, ext_info=None):
        self.receiver_list = receiver_list
        self.mes_content = mes_content
        self.ext_info = ext_info
        self.config = current_app.config

    def sendEmail(self):
        """
        发送邮件通知
        """

        @copy_current_request_context
        def send_async_email(to, subject, template):
            msg = Message(
                subject,
                recipients=[to],
                html=template,
                sender=self.config.get('MAIL_DEFAULT_SENDER')
            )
            #发送邮件
            mail.send(msg)


        for receiver in self.receiver_list:
            html = render_template('email/email.html', receiver=receiver, ext_info=self.ext_info, mes_content=self.mes_content)
            subject = '[AUD]' + self.mes_content

            thr = Thread(target=send_async_email, args=[receiver + '@aicai.com', subject, html])
            thr.start()

            #保存发送记录
            message_record = app.models.Message_log(receiver=receiver,
                                                status=1,    #邮件通知状态为已发送
                                                type=1,    #邮件通知类型为1
                                                mes_content=self.mes_content,
                                                create_time=datetime.now(),
                                                ext_info=self.ext_info)
            message_record.save()

    def sendInstationMes(self):
        """
        发送站内通知
        """
        for receiver in self.receiver_list:
            message_record = app.models.Message_log(receiver=receiver,
                                                status=0,    #站内通知初始状态为未读
                                                type=0,    #站内通知类型为0
                                                mes_content=self.mes_content,
                                                create_time=datetime.now(),
                                                ext_info=self.ext_info)
            message_record.save()

    def sendSMS(self):
        """
        发送短信通知
        """
        pass



