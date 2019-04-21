# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from basic import models as basic_models


# Create your models here.
class AttendanceRate(models.Model):  # 考勤出勤率
    give_time = models.CharField(max_length=64)  # '年月','2019-03'
    staff = models.ForeignKey('basic.Staff')
    attendance_rate = models.FloatField()  # 出勤率


class TeachRoll(models.Model):  # 教学细项工资管理（教学加班，德育补助，安全补助等等）
    staff = models.ForeignKey(basic_models.Staff)
    item = models.ForeignKey(basic_models.TeachItem)  # 注意这个是teachitem
    teach_time = models.FloatField(default='0')  # 教学课时支持浮点数
    the_price = models.FloatField(default='0')  # 当时这条课时记录的课时单价
    money = models.FloatField()  # 教学细项工资记录的价格
    give_time = models.CharField(max_length=64)  # '年月'
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        # unique_together = ('staff', 'teach_time', 'give_time')  # 同员工同条目同年月工资记录不可重复
        unique_together = ('staff', 'item', 'give_time')  # 同员工同条目同年月工资记录不可重复


class Payroll(models.Model):  # 工资记录
    staff = models.ForeignKey(basic_models.Staff)
    item = models.ForeignKey(basic_models.Item)
    money = models.FloatField(default=-1)
    give_time = models.CharField(max_length=64)  # '年月','2019-03'
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now_add=True)
    verify = models.ForeignKey('WaitVerify')  # 外键到工资审核记录

    class Meta:
        unique_together = ('staff', 'item', 'give_time')  # 同员工同条目同年月工资记录不可重复


# 财务部按提交者进行审核
# 最后决定每月统计一次课时记录
# 现在A主管管理三个部门的稿费，流程是一个一个部门处理好，最后点个申请审核，如果处理了一个部门，就审核了，
# 那其他部门录入时就拒绝
# 如果a老师和b老师共同管理n个部门n条条目的，他们只能用同一个账号，不然会有事发生
class WaitVerify(models.Model):  # 工资审核记录，在放记录确认发放之前，都可以撤回审核
    give_time = models.CharField(max_length=64)  # '年月','2019-03'
    work_user = models.ForeignKey(User)  # 操作人
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now_add=True)
    verify = models.IntegerField(choices=((0, '待审核'), (1, '审核通过'), (2, '审核拒绝'), (3, '暂存')),
                                 default=3)  # 暂存的财务不可见


class PayrollRecords(models.Model):  # 工资发放记录
    give_time = models.CharField(max_length=64)  # '年月','2019-03'
    final_salary = models.FloatField(default=0)
    pay_date = models.DateField(max_length=64, null=True)  # 改了
    status = models.IntegerField(choices=((0, '未发放'), (1, '已发放')), default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now_add=True)
