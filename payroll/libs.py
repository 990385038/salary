# -*- coding:utf-8 -*-

import json

from django.db.models import Sum
from django.http import HttpResponseBadRequest

from payroll import models


#  传入年月，计算该年月所有薪水记录应发和-应扣和
# 在添该单条薪水记录时调用，所以第一个if成立。
def final_salary(give_time):
    final = 0
    if models.WaitVerify.objects.filter(give_time=give_time, verify=1).exists():
        wait_obj = models.WaitVerify.objects.get(give_time=give_time, verify=1)
        final_yf = 0
        final_yk = 0
        # 薪水记录type:1应发，2应扣
        if models.Payroll.objects.filter(give_time=give_time, verify=wait_obj, item__type=1).exists():
            # final_yf = models.Salary.objects.filter(give_time=give_time,
            #                                         item__type=1).values('give_time').annotate(
            #     yfsum=Sum('money'))[0]['yfsum']   # 根据give_time分组并计算各组money的和yfsum,给每个记录加一个yfsum
            # aggregate:对所有记录的money求和，并组成键值对{'money':**}
            final_yf = models.Payroll.objects.filter(give_time=give_time, item__type=1).aggregate(a=Sum('money'))['a']
        if models.Payroll.objects.filter(give_time=give_time, verify=wait_obj, item__type=2).exists():
            # final_yk = models.Salary.objects.filter(give_time=give_time,
            #                                         item__type=0).values('give_time').annotate(
            #     yksum=Sum('money'))[0]['yksum']
            final_yk = models.Payroll.objects.filter(give_time=give_time, item__type=2).aggregate(a=Sum('money'))['a']
        final = final_yf - final_yk
        return final
    else:
        return final


# 传入年月，拿年月去查该年月薪水记录应发-应扣之和，有薪水发放记录就更新，没有就新建薪水发放记录并更新
def freash_payroll_records(give_time):
    if models.PayrollRecords.objects.filter(give_time=give_time).exists():
        re = models.PayrollRecords.objects.get(give_time=give_time)
    else:
        re = models.PayrollRecords()
    re.give_time = give_time
    re.final_salary = final_salary(give_time)
    re.save()


# 该提交者该年月，工资审核状态为暂存或失败时才可以做一些事
def check_verify(give_time, user):
    if not models.WaitVerify.objects.filter(give_time=give_time, work_user=user, verify=3).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'data': [],
                                                  'msg': '审核记录不为暂存，请先撤回审核'}),
                                      content_type='application/json')


# 该年月，工资发放记录为未创建或者未发放才可以做一些事
def check_payroll_records(give_time):
    if models.PayrollRecords.objects.filter(give_time=give_time, status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '该年月工资记录已确认发放，不可以再审批通过', 'data': []})
                                      , content_type='application/json')
