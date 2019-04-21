# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import django
import random
import datetime
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sh_salary.settings")
django.setup()






from faker import Faker
from basic import models
# from faker.providers import BaseProvider  # 引入基类

fake = Faker('zh-CN')


def create_staff():
    for i in range(50):  # 对Staff模型
        try:
            staff_obj = models.Staff()
            staff_obj.id_card = fake.ssn(min_age=18, max_age=90)
            staff_obj.name = fake.name()
            staff_obj.phone = fake.phone_number()
            staff_obj.bank_card_num = fake.bban()
            staff_obj.bank_name = '测试银行'
            staff_obj.entry_date = datetime.datetime.strptime('2019-01-01', '%Y-%m-%d')
            staff_obj.tax_start = random.randint(5, 10) * 1000
            staff_obj.department = models.Department.objects.get(id=random.randint(5,9))
            staff_obj.remark = '测试'
            staff_obj.save()
            print('生成数量:{}'.format(models.Staff.objects.all().count()))
        except Exception as e:
            print(e)
            continue
create_staff()