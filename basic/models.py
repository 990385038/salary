# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Staff(models.Model):
    id_card = models.CharField(unique=True, max_length=32)
    name = models.CharField(max_length=64)
    phone = models.CharField(max_length=64)
    bank_card_num = models.CharField(max_length=64)
    bank_name = models.CharField(max_length=64)
    entry_date = models.DateTimeField()  # 入职时间
    tax_start = models.FloatField(default=5000)  # 个税起征点
    status = models.IntegerField(choices=((0, '离职'), (1, '在职')), default=1)
    department = models.ForeignKey('Department')
    remark = models.CharField(max_length=64, default='')


class Department(models.Model):
    name = models.CharField(unique=True, max_length=64)
    remark = models.CharField(max_length=64)
    status = models.IntegerField(choices=((0, '无效'), (1, '有效')), default=1)


class Item(models.Model):  # 简单处理条目名不能重复，等作用id，条目可以重名
    type = models.IntegerField(choices=((0, '应扣'), (1, '应发')))
    # 应发：标准、教学、其他工资，三项细节会汇入教学工资，小学三项，中学三项，用课类模型进行管理
    # 基本工资、职位工资、绩效工资、周年补助、考勤、水电费、外宿、工会经费、稿件费
    sec_type = models.IntegerField(choices=
                                   ((0, '应扣'), (1, '标准工资'), (2, '教学工资'), (3, '其他工资')))
    name = models.CharField(max_length=32)  # 条目名唯一
    status = models.IntegerField(choices=((0, '无效'), (1, '有效')), default=1)
    remark = models.CharField(max_length=64, default='')


# class DefaultPayroll(models.Model):  # 默认工资 # 取消
#     item = models.ForeignKey('Item')
#     money = models.FloatField()
#     staff = models.ForeignKey('Staff')


class File(models.Model):  # 文档模型
    name = models.CharField(max_length=64)
    staff = models.ForeignKey('Staff', related_name='file')
    qiniu_name = models.CharField(max_length=64)
    remark = models.CharField(max_length=64, default='')


# 教学细项
class TeachItem(models.Model):  # 教学细项管理：教学加班（含默认教学课时费）、德育补助、安全补助等等。
    item = models.ForeignKey(Item)
    type = models.IntegerField(choices=((0, '计课时'), (1, '计总费')))
    name = models.CharField(max_length=64)
    default_price = models.CharField(max_length=64, default='')  # 计课时才有
    remark = models.CharField(max_length=64, default='')
    status = models.IntegerField(choices=((0, '无效'), (1, '有效')), default=1)

    class Meta:
        unique_together = ('item', 'type', 'name')  # 最新发现utf8mb4才出现索引问题，改了字段长度要全部删掉重新迁移，
        # 或者改数据库为utf8mb4


class UnitPrice(models.Model):  # 关联员工的教学课时费记录
    course = models.ForeignKey('TeachItem')
    staff = models.ForeignKey('Staff')
    price = models.FloatField(default=0)

    class Meta:
        unique_together = ('course', 'staff')


class ItemUser(models.Model):  # 条目(含细项)用户权限模型
    item = models.ForeignKey(Item)
    user = models.ForeignKey(User)
