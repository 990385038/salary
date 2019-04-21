# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import transaction  # 原子操作
from django.http import HttpResponseBadRequest, HttpResponse

from basic import models as basic_models
from payroll import forms, models, libs


# Create your views here.
def bulk_add_attendance(request):  # 批量添改生成某年月某部门出勤率,参考某年月,直接生成
    form = forms.BulkAddattendance(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    staff_query_set = basic_models.Staff.objects.filter(department=form.cleaned_data['department'], status=1)
    for i in staff_query_set:
        if models.AttendanceRate.objects.filter(give_time=form.cleaned_data['refer_time'], staff=i.id).exists():
            rate = models.AttendanceRate.objects.get(give_time=form.cleaned_data['refer_time'],
                                                     staff=i.id).attendance_rate
        else:
            rate = 0
        if not models.AttendanceRate.objects.filter(give_time=form.cleaned_data['give_time'], staff=i).exists():
            models.AttendanceRate.objects.create(give_time=form.cleaned_data['give_time'], staff=i,
                                                 attendance_rate=rate)
        else:
            the_obj = models.AttendanceRate.objects.get(give_time=form.cleaned_data['give_time'], staff=i)
            the_obj.attendance_rate = rate
            the_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '批量生成出勤率成功', 'data': []}),
                        content_type='application/json')


def edit_attendance(request):
    form = forms.EditAttendance(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.AttendanceRate.objects.filter(id=form.cleaned_data['id']).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要编辑的出勤率不存在', 'data': []}),
                                      content_type='application/json')
    attendance_rate = models.AttendanceRate.objects.get(id=form.cleaned_data['id'])
    attendance_rate.attendance_rate = form.cleaned_data['rate']
    attendance_rate.save()
    json_dic = {'code': 'ok', 'msg': '编辑考勤记录成功', 'data': []}
    return HttpResponse(json.dumps(json_dic), content_type='application/json')


def all_attendance(request):  # 查某部门某年月考勤记录
    form = forms.AllAttendance(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    query_set = models.AttendanceRate.objects.select_related('staff').filter(give_time=form.cleaned_data['give_time'],
                                                                             staff__department=form.cleaned_data[
                                                                                 'department'])
    data_list = list()
    for i in query_set:
        one_rate_dic = dict()
        one_rate_dic['id'] = i.id
        one_rate_dic['staff_name'] = i.staff.name
        one_rate_dic['attendance_rate'] = i.attendance_rate
        data_list.append(one_rate_dic)
    json_dic = {'code': 'ok', 'msg': '查询考勤记录成功', 'data': data_list}
    return HttpResponse(json.dumps(json_dic), content_type='application/json')


# 对指定部门所有员工、指定[条目]、指定年月的工资记录进行预览
def payroll_preview(request):
    form = forms.PayrollPrevies(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    department_id = form.cleaned_data['department_id']
    give_time = form.cleaned_data['refer_time']
    items = form.cleaned_data['items_id'].split('|')
    staff_set = basic_models.Staff.objects.filter(department=department_id, status=1)
    item_obj_list = list()
    item_set = basic_models.ItemUser.objects.filter(user=request.user)  # 查出用户当前有权限查看的条目
    item_list = list()
    for i in item_set:
        item_list.append(i.item_id)  # 得出可以对用户展示的工资记录
    for i in items:  # 得到id对象的列表
        if not basic_models.Item.objects.filter(id=i, status=1).exists():
            return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '工资查询的条目不存在', 'data': []}),
                                          content_type='application/json')
        if basic_models.Item.objects.get(id=i).name in ['教学加班', '德育补助', '安全补助']:
            return HttpResponseBadRequest(
                json.dumps({'code': 'false', 'msg': '教学加班,德育补助和安全补助三项工资要到三项管理处管理',
                            'data': []}), content_type='application/json')
        if int(i) not in item_list:
            return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '用户权限不可以查看该条目', 'data': []}),
                                          content_type='application/json')
        item_obj_list.append(basic_models.Item.objects.get(id=i))
    cols_list = [{'prop': 'id_card', 'label': '身份证'}, {'prop': 'name', 'label': '姓名'}]  # 列定义
    for j in item_obj_list:  # 对条目对象列表遍历
        cols_list.append({'prop': str(j.id), 'label': j.name})  # 处理列定义
    each_row = list()
    for i in staff_set:  # 对员工进行遍历
        one_staff_dic = dict()
        one_staff_dic['staff_id'] = i.id
        one_staff_dic['id_card'] = i.id_card
        one_staff_dic['name'] = i.name
        for j in item_obj_list:  # 对条目对象列表遍历
            if models.Payroll.objects.filter(staff=i, item=j, give_time=give_time).exists():
                money = models.Payroll.objects.get(staff=i, item=j, give_time=give_time).money
            else:
                money = 0
            one_staff_dic[j.id] = money
        each_row.append(one_staff_dic)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '对指定部门选定条目、指定年月的工资记录进行查询成功',
                                    'data': {'each_row': each_row, 'cols_list': cols_list}}),
                        content_type='application/json')


# 对用户,展示某年月某部门当月工资记录
def payroll_view(request):
    form = forms.PayrollView(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    department_id = form.cleaned_data['department']
    give_time = form.cleaned_data['give_time']
    item_set = basic_models.ItemUser.objects.filter(user=request.user)  # 查出用户当前有权限查看的条目
    item_list = list()
    for i in item_set:
        item_list.append(i.item_id)
    # 得出可以展示的工资记录
    salary_queryset = models.Payroll.objects.select_related('staff', 'item').filter(staff__department_id=department_id,
                                                                                    give_time=give_time,
                                                                                    item_id__in=item_list)
    cols_list = [{'prop': 'id_card', 'label': '身份证'}, {'prop': 'name', 'label': '姓名'},
                 {'prop': 'id', 'label': '员工id'}]
    item_list = list(salary_queryset.values('item_id', 'item__name').order_by('item__sec_type',
                                                                              'item_id').distinct())
    for i in item_list:
        cols_list.append({'prop': str(i['item_id']), 'label': i['item__name']})  # 得到列定义
    # 基于工资记录的员工
    staff_query = list(salary_queryset.values('staff_id', 'staff__name', 'staff__id_card').order_by(
        'staff_id').distinct())
    each_row = list()
    for j in staff_query:  # 获取所有当月有效员工的id，身份证和名字
        one_row = dict()
        one_row['id'] = j['staff_id']
        one_row['id_card'] = j['staff__id_card']
        one_row['name'] = j['staff__name']
        each_payroll = list(
            salary_queryset.filter(staff_id=j['staff_id']).values('item__id', 'money').order_by(
                'item__sec_type', 'item_id'))
        # 用vue这种动态列方法，不用遍历条目去orm操作
        # {'data':{'each_row':[{'id_card':'*','条目id':金额]......},'cols_list':[{'prop':'id_card','label':'身份证'},......]}}
        for k in each_payroll:
            one_row.update({str(k['item__id']): k['money']})  # 得到{'id_card':'*','条目id':条目的钱,......}
        each_row.append(one_row)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '查询年月部门工资成功',
                                    'data': {'each_row': each_row, 'cols_list': cols_list}}),
                        content_type='application/json')


# 不从前端获取json了，即不能批量编辑返回json
def bulk_add_payroll(request):
    # form = forms.BulkAddPayroll(request.POST)
    # if not form.is_valid():
    #     e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
    #     return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
    #                                   content_type='application/json')
    # json_data = json.loads(form.cleaned_data['json_data_str'])
    # give_time = json_data['give_time']
    # staff_list = json_data['each_staff']
    # # json_data = json.loads(request.POST.get('json_data_str'))  # json_schema配置不好，不使用json_schema校验
    # 后来发现json_schema校验可以在线生成
    # # give_time = json_data['give_time']
    # # staff_list = json_data['each_staff']
    # try:
    #     with transaction.atomic():  # 原子操作
    #         if not models.WaitVerify.objects.filter(work_user=request.user, give_time=give_time).exists():
    #             models.WaitVerify.objects.create(work_user=request.user, give_time=give_time)  # 创建暂存工资审核记录
    #         wait_verify_obj = models.WaitVerify.objects.get(work_user=request.user, give_time=give_time)
    #         for i in staff_list:
    #             if not basic_models.Staff.objects.filter(id=i, status=1).exists():
    #                 return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '员工不存在', 'data': []}),
    #                                               content_type='application/json')
    #             staff_obj = basic_models.Staff.objects.get(staff=i)
    #             for j in i['items']:
    #                 if not basic_models.Item.objects.filter(id=j['item_id'], status=1).exists():
    #                     return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '条目不存在', 'data': []}),
    #                                                   content_type='application/json')
    #                 item_obj = basic_models.Item.objects.get(id=j['item_id'], status=1)
    #                 if not models.Payroll.objects.filter(staff=staff_obj, item=item_obj, give_time=give_time).exists:
    #                     models.Payroll.objects.create(staff=staff_obj, item=item_obj, money=j['money'],
    #                                                   give_time=give_time, verify=wait_verify_obj)
    #                 else:
    #                     payroll_obj = models.Payroll.objects.get(staff=staff_obj, item=item_obj, give_time=give_time)
    #                     payroll_obj.update(money=j['money'])
    #         return HttpResponse(json.dumps({'code': 'ok', 'msg': '对指定部门选定条目、指定年月的工资记录生成成功',
    #                                         'data': staff_list}), content_type='application/json')
    # except Exception as e:
    #     return HttpResponseBadRequest(json.dumps({'code': 'ok', 'msg': e, 'data': staff_list}),
    #                                   content_type='application/json')
    form = forms.BulkAddPayroll(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'misg': e, 'data': []}),
                                      content_type='application/json')
    item_id_list = [int(x) for x in form.cleaned_data['items_id'].split('|')]
    item_obj_list = list()
    for i in item_id_list:
        if not basic_models.Item.objects.filter(id=i, status=1).exists():
            return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '条目不存在', 'data': []}),
                                          content_type='application/json')
        if basic_models.Item.objects.get(id=i).name in ['教学加班', '德育补助', '安全补助']:
            return HttpResponseBadRequest(
                json.dumps({'code': 'false', 'msg': '教学加班,德育补助和安全补助三项工资要到三项管理处管理',
                            'data': []}), content_type='application/json')
        item_obj_list.append(basic_models.Item.objects.get(id=i, status=1))
    refer_time = form.cleaned_data['refer_time']  #
    give_time = form.cleaned_data['give_time']  #
    staff_list = basic_models.Staff.objects.filter(department=form.cleaned_data['department_id'], status=1)
    try:
        with transaction.atomic():  # 原子操作
            if not models.WaitVerify.objects.filter(work_user=request.user, give_time=give_time).exists():
                models.WaitVerify.objects.create(work_user=request.user, give_time=give_time)  # 创建暂存工资审核记录
            wait_verify_obj = models.WaitVerify.objects.get(work_user=request.user, give_time=give_time)
            for i in staff_list:
                for j in item_obj_list:
                    if models.Payroll.objects.filter(staff=i, item=j, give_time=refer_time).exists():
                        money = models.Payroll.objects.get(staff=i, item=j, give_time=refer_time).money
                    else:
                        money = 0
                    if not models.Payroll.objects.filter(staff=i, item=j, give_time=give_time).exists():
                        models.Payroll.objects.create(staff=i, item=j, money=money, give_time=give_time,
                                                      verify=wait_verify_obj)
                    else:  # 若要生成年月的工资已有则覆盖金额，一般不会有这个情况，两次批量生成操作就会有
                        the_payroll_obj = models.Payroll.objects.get(staff=i, item=j, give_time=give_time)
                        the_payroll_obj.money = money
                        the_payroll_obj.save()
            return HttpResponse(json.dumps({'code': 'ok', 'msg': '对指定部门选定条目、指定年月的工资记录生成成功',
                                            'data': []}), content_type='application/json')
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'code': 'ok', 'msg': e, 'data': staff_list}),
                                      content_type='application/json')


# 预览（教学加班，德育补助，安全补助dd）细项
def teachroll_priview(request):
    form = forms.TeachrollPreview(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    item_ch = form.cleaned_data['item_ch']
    teahitem_list = [int(x) for x in form.cleaned_data['teachitem_id'].split('|')]  # ['1','2','3']变 [1,2,3]
    if not basic_models.Item.objects.filter(name=item_ch, status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '条目{}无效'.format(item_ch), 'data': []}),
                                      content_type='application/json')
    the_item_id = basic_models.Item.objects.get(name=item_ch, status=1).id
    if not basic_models.ItemUser.objects.filter(user=request.user, item__id=the_item_id).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '用户权限不可管理该条目', 'data': []}),
                                      content_type='application/json')
    for i in teahitem_list:
        if not basic_models.TeachItem.objects.filter(id=i, status=1).exists():
            return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '存在细项无效', 'data': []}),
                                          content_type='application/json')
    department_id = form.cleaned_data['department']
    refer_time = form.cleaned_data['refer_time']
    # teachitem_set = basic_models.TeachItem.objects.filter(item=the_item_id, status=1)  # 某条目的所有细项
    time_teachitem_set = basic_models.TeachItem.objects.filter(id__in=teahitem_list, status=1, type=0)  # 条目的计课时细项
    notime_teachitem_set = basic_models.TeachItem.objects.filter(id__in=teahitem_list, status=1, type=1)  # 条目的非计课时细项
    cols_list = [{'prop': 'id_card', 'label': '身份证'}, {'prop': 'name', 'label': '姓名'}]  # 列定义
    for j in time_teachitem_set:  # 对条目对象列表遍历
        cols_list.append({'prop': str(j.id), 'label': j.name})  # 处理所有细项列定义
    for j in notime_teachitem_set:  # 对条目对象列表遍历
        cols_list.append({'prop': str(j.id), 'label': j.name})  # 处理所有细项列定义
    staff_set = basic_models.Staff.objects.filter(department=department_id, status=1)
    each_row = list()
    for i in staff_set:
        one_staff_dic = dict()
        one_staff_dic['staff_id'] = i.id
        one_staff_dic['id_card'] = i.id_card
        one_staff_dic['name'] = i.name
        # 要遍历去找，现在的细项和当时的细项可能有差异
        for j in time_teachitem_set:  # 计课时的细项
            if models.TeachRoll.objects.filter(staff=i, item=j, give_time=refer_time).exists():
                one_staff_dic[j.id] = str(models.TeachRoll.objects.get(staff=i, item=j,
                                                                       give_time=refer_time).teach_time)
            else:
                one_staff_dic[j.id] = "0"
            if basic_models.UnitPrice.objects.filter(course=j, staff=i).exists():
                one_staff_dic[j.id] = one_staff_dic[j.id] + "*" + str(
                    basic_models.UnitPrice.objects.get(course=j, staff=i).price)
            else:
                one_staff_dic[j.id] = one_staff_dic[j.id] + "*" + "0"
        for j in notime_teachitem_set:
            if models.TeachRoll.objects.filter(staff=i, item=j, give_time=refer_time).exists():
                money = models.TeachRoll.objects.get(staff=i, item=j, give_time=refer_time).money
            else:
                money = 0
            one_staff_dic[j.id] = money
        each_row.append(one_staff_dic)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '对指定部门选定条目、指定年月的工资细项进行查询成功',
                                    'data': {'each_row': each_row, 'cols_list': cols_list}}),
                        content_type='application/json')


# 用户查询某部门某年月的"教学加班"，"德育补助","安全补助"条目的细项统计
def teachroll_view(request):
    form = forms.TeachView(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    department_id = form.cleaned_data['department']
    give_time = form.cleaned_data['give_time']
    item_ch = form.cleaned_data['item_ch']
    if not basic_models.Item.objects.filter(name=item_ch, status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '条目{}无效'.format(item_ch), 'data': []}),
                                      content_type='application/json')
    the_item_id = basic_models.Item.objects.get(name=item_ch, status=1).id
    if not basic_models.ItemUser.objects.filter(user=request.user, item__id=the_item_id).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '用户权限不可管理该条目', 'data': []}),
                                      content_type='application/json')
    teachroll_set = models.TeachRoll.objects.select_related('staff', 'item').filter(staff__department_id=department_id,
                                                                                    give_time=give_time,
                                                                                    item__item_id=the_item_id)
    cols_list = [{'prop': 'id_card', 'label': '身份证'}, {'prop': 'name', 'label': '姓名'},
                 {'prop': 'id', 'label': '员工id'}]
    teach_item_list = list(teachroll_set.values('item_id', 'item__name').order_by('item__type').distinct())
    for i in teach_item_list:
        cols_list.append({'prop': str(i['item_id']), 'label': i['item__name']})  # 得到列定义,身份证，姓名，细项名...
    # 基于工资细项记录的员工
    staff_query = list(teachroll_set.values('staff_id', 'staff__name', 'staff__id_card').order_by(
        'staff_id').distinct())
    each_row = list()
    for j in staff_query:  # 获取所有当月有效用户的id，身份证和名字
        one_row = dict()
        one_row['id'] = j['staff_id']
        one_row['id_card'] = j['staff__id_card']
        one_row['name'] = j['staff__name']
        each_time_teachroll = list(
            teachroll_set.filter(staff_id=j['staff_id'], item__type=0).values('item__id', 'the_price', 'teach_time'))
        each_notime_teachroll = list(
            teachroll_set.filter(staff_id=j['staff_id'], item__type=1).values('item__id', 'money'))
        # 用vue这种动态列方法，不用遍历条目去orm操作
        # {'data':{'each_row':[{'id_card':'*','条目id':金额]......},'cols_list':[{'prop':'id_card','label':'身份证'},......]}}
        for k in each_time_teachroll:
            one_row.update({str(k['item__id']): str(k['the_price']) + '*' + str(k['teach_time'])})
        for k in each_notime_teachroll:
            one_row.update({str(k['item__id']): k['money']})
        # 得到{'id_card':'*','条目id':条目的钱,......}
        each_row.append(one_row)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '查询年月部门工资细项成功',
                                    'data': {'each_row': each_row, 'cols_list': cols_list}}),
                        content_type='application/json')


# 不从前端获取json了，即不能批量编辑返回json
def bulk_add_teachroll(request):
    # form = forms.BulkAddTeachroll(request.POST)
    # if not form.is_valid():
    #     e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
    #     return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
    #                                   content_type='application/json')
    # json_data = json.loads(form.cleaned_data['json_data_str'])
    # give_time = json_data['give_time']
    # item_id = json_data['item_id']
    # item_money = json_data['item_money']  # 条目总钱及细项都要发，
    # staff_list = json_data['each_staff']
    # try:
    #     with transaction.atomic():  # 原子操作
    #         if not models.WaitVerify.objects.filter(work_user=request.user, give_time=give_time).exists():
    #             models.WaitVerify.objects.create(work_user=request.user, give_time=give_time)  # 创建暂存工资审核记录
    #         wait_verify_obj = models.WaitVerify.objects.get(work_user=request.user, give_time=give_time)
    #         for i in staff_list:
    #             if not basic_models.Staff.objects.filter(id=i, status=1).exists():
    #                 return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '员工不存在', 'data': []}),
    #                                               content_type='application/json')
    #             staff_obj = basic_models.Staff.objects.get(staff=i)
    #             if not models.Payroll.objects.filter(staff=i, item=item_id, give_time=give_time).exists():
    #                 models.Payroll.objects.create(staff=i, item=item_id, money=item_money, give_time=give_time,
    #                                               verify=wait_verify_obj)
    #             else:  # 处理该（教学加班、德育、安全等等）的记录暂存
    #                 models.Payroll.objects.get(staff=i, item=item_id, give_time=give_time).update(money=item_money)
    #             for j in i['teachitems_hour']:
    #                 if not basic_models.TeachItem.objects.filter(id=j['item_id'], status=1).exists():
    #                     return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '细项不存在', 'data': []}),
    #                                                   content_type='application/json')
    #                 teachitem_obj = basic_models.TeachItem.objects.get(id=j['teachitem_id'], status=1)
    #                 if not models.Payroll.objects.filter(staff=staff_obj, item=teachitem_obj,
    #                                                      give_time=give_time).exists():
    #                     models.TeachRoll.objects.create(staff=staff_obj, item=teachitem_obj, teach_time=j['teach_time'],
    #                                                     give_time=give_time, verify=wait_verify_obj)
    #                 else:
    #                     teachpayroll_obj = models.TeachRoll.objects.get(staff=staff_obj, item=teachitem_obj,
    #                                                                     give_time=give_time)
    #                     teachpayroll_obj.update(money=j['money'])
    #             for j in i['teachitems_nohour']:
    #                 if not basic_models.TeachItem.objects.filter(id=j['item_id'], status=1).exists():
    #                     return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '细项不存在', 'data': []}),
    #                                                   content_type='application/json')
    #                 teachitem_obj = basic_models.TeachItem.objects.get(id=j['teachitem_id'], status=1)
    #                 if not models.Payroll.objects.filter(staff=staff_obj, item=teachitem_obj,
    #                                                      give_time=give_time).exists():
    #                     models.TeachRoll.objects.create(staff=staff_obj, item=teachitem_obj, teach_time=j['teach_time'],
    #                                                     give_time=give_time, verify=wait_verify_obj)
    #                 else:
    #                     teachpayroll_obj = models.TeachRoll.objects.get(staff=staff_obj, item=teachitem_obj,
    #                                                                     give_time=give_time)
    #                     teachpayroll_obj.update(money=j['money'])
    #         return HttpResponse(json.dumps({'code': 'ok', 'msg': '对指定部门选定条目、指定年月的教学细项记录和条目'
    #                                                              '工资记录生成成功',
    #                                         'data': staff_list}), content_type='application/json')
    # except Exception as e:
    #     return HttpResponseBadRequest(json.dumps({'code': 'ok', 'msg': e, 'data': []}),
    #                                   content_type='application/json')
    form = forms.BulkAddTeachroll(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    item_ch = form.cleaned_data['item_ch']
    if not basic_models.Item.objects.filter(name=item_ch, status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '条目{}无效'.format(item_ch), 'data': []}),
                                      content_type='application/json')
    the_item_id = basic_models.Item.objects.get(name=item_ch, status=1).id
    if not basic_models.ItemUser.objects.filter(user=request.user, item__id=the_item_id).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '用户权限不可管理该条目', 'data': []}),
                                      content_type='application/json')
    teachitem_list = [int(x) for x in form.cleaned_data['teachitem_id'].split('|')]
    teach_houritem_set = basic_models.TeachItem.objects.filter(id__in=teachitem_list, status=1, type=0)
    teach_nohouritem_set = basic_models.TeachItem.objects.filter(id__in=teachitem_list, status=1, type=1)
    refer_time = form.cleaned_data['refer_time']
    give_time = form.cleaned_data['give_time']
    libs.check_verify(give_time, request.user)
    libs.freash_payroll_records(give_time)
    staff_list = basic_models.Staff.objects.filter(department=form.cleaned_data['department_id'], status=1)
    try:
        with transaction.atomic():  # 原子操作
            if not models.WaitVerify.objects.filter(work_user=request.user, give_time=give_time).exists():
                models.WaitVerify.objects.create(work_user=request.user, give_time=give_time)  # 创建暂存工资审核记录
            wait_verify_obj = models.WaitVerify.objects.get(work_user=request.user, give_time=give_time)
            for i in staff_list:
                # 计时的细项
                item_payroll = 0
                for j in teach_houritem_set:
                    if models.TeachRoll.objects.filter(staff=i, item=j, give_time=refer_time).exists():
                        teach_time = models.TeachRoll.objects.get(staff=i, item=j, give_time=refer_time).teach_time
                    else:
                        teach_time = 0  # 取参考月课时
                    if basic_models.UnitPrice.objects.filter(course=j, staff=i).exists():
                        teachitem_price = basic_models.UnitPrice.objects.get(course=j, staff=i).price
                    else:
                        teachitem_price = 0  # 取员工的该课时费
                    money = teach_time * teachitem_price  # 那项细节条目工资的金额
                    item_payroll += money
                    if not models.TeachRoll.objects.filter(staff=i, item=j, give_time=refer_time).exists():
                        models.TeachRoll.objects.create(staff=i, item=j, teach_time=teach_time,
                                                        the_price=teachitem_price,
                                                        money=money, give_time=give_time)
                    else:  # 若要生成年月的细节工资条目已有则覆盖
                        the_payroll_obj = models.TeachRoll.objects.get(staff=i, item=j, give_time=give_time)
                        the_payroll_obj.money = money
                        the_payroll_obj.teach_time = teach_time
                        the_payroll_obj.the_price = teachitem_price
                        the_payroll_obj.save()
                # 非计时的细项
                for j in teach_nohouritem_set:
                    if models.TeachRoll.objects.filter(staff=i, item=j, give_time=refer_time).exists():
                        money = models.TeachRoll.objects.get(staff=i, item=j, give_time=refer_time).money
                    else:
                        money = 0  # 取参考月费用，非计时取总费
                    if not models.TeachRoll.objects.filter(staff=i, item=j, give_time=give_time).exists():
                        models.TeachRoll.objects.create(staff=i, item=j, money=money, give_time=give_time)
                    else:
                        the_payroll_obj = models.TeachRoll.objects.get(staff=i, item=j, give_time=give_time)
                        the_payroll_obj.money = money
                        the_payroll_obj.save()
                item_obj = basic_models.Item.objects.get(name=form.cleaned_data['item_ch'])
                # 处理条目的工资记录,暗自处理
                if not models.Payroll.objects.filter(staff=i, item=item_obj).exists():
                    models.Payroll.objects.create(staff=i, item=item_obj, money=item_payroll, give_time=give_time,
                                                  verify=wait_verify_obj)
                else:
                    item_payroll_obj = models.Payroll.objects.get(staff=i, item=item_obj)
                    item_payroll_obj.money = item_payroll
                    item_payroll_obj.save()
            return HttpResponse(json.dumps({'code': 'ok', 'msg': '对指定部门选定条目、指定年月的工资记录生成成功',
                                            'data': []}), content_type='application/json')
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')


# 申请审批工资记录，某用户对某年月提交审核
def ask_payroll_verify(request):
    form = forms.AskPayrollVerify(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.WaitVerify.objects.filter(give_time=form.cleaned_data['give_time'], work_user=request.user).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '未暂存任何待审核记录', 'data': []}),
                                      content_type='application/json')
    else:
        models.WaitVerify.objects.filter(give_time=form.cleaned_data['give_time'], work_user=request.user).update(
            verify=0)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '申请审批工资记录成功', 'data': []}),
                        content_type='application/json')


# 撤销工资审核
# 未审核，审核通过，审核拒绝，暂存，全部可以撤销审核改为暂存
def cancel_payroll_verify(request):
    form = forms.EditPayrollVerify(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.WaitVerify.objects.filter(give_time=form.cleaned_data['give_time'], work_user=request.user).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '申请审批的工资记录不存在', 'data': []}),
                                      content_type='application/json')
    payroll_obj = models.WaitVerify.objects.get(give_time=form.cleaned_data['give_time'], work_user=request.user)
    payroll_obj.verify = 2
    payroll_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '取消申请审批工资记录成功', 'data': []}),
                        content_type='application/json')


def effect_payroll_verify(request):
    verify_set = models.WaitVerify.objects.filter(verify=0)
    data_list = list()
    for i in verify_set:
        each_dic = dict()
        each_dic['id'] = i.id
        each_dic['give_time'] = i.give_time
        each_dic['work_user'] = i.work_user.first_name
        each_dic['create_time'] = i.update_time.strftime('%Y-%m-%d')
        data_list.append(each_dic)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '查询待审核工资记录成功', 'data': data_list}),
                        content_type='application/json')


def all_payroll_verify(request):
    verify_set = models.WaitVerify.objects.all().exclude(verify=3)
    data_list = list()
    for i in verify_set:
        each_dic = dict()
        each_dic['id'] = i.id
        each_dic['give_time'] = i.give_time
        each_dic['work_user'] = i.work_user.first_name
        each_dic['verify'] = i.get_verify_display()
        each_dic['create_time'] = i.update_time.strftime('%Y-%m-%d')
        data_list.append(each_dic)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '查询所有审核工资记录成功', 'data': data_list}),
                        content_type='application/json')


def compare_payroll(request):
    form = forms.ComparePayroll(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    verify_id = form.cleaned_data['verify_id']
    give_time = form.cleaned_data['give_time']
    refer_time = form.cleaned_data['refer_time']
    staff_id_set = models.Payroll.objects.filter(verify_id=verify_id).values('staff_id').distinct().order_by('staff_id')
    staff_id_list = list()
    for i in staff_id_set:
        staff_id_list.append(i['staff_id'])
    item_id_set = models.Payroll.objects.filter(verify_id=verify_id).values('item_id').distinct().order_by(
        'item_id')
    item_id_list = list()
    cols_list = [{'prop': 'id_card', 'label': '身份证'}, {'prop': 'name', 'label': '姓名'}]
    for i in item_id_set:  # 生成列定义和item的id列表
        item_id_list.append(i['item_id'])
        one_col_dic = dict()
        one_col_dic['prop'] = i.id
        one_col_dic['label'] = i.name
        cols_list.append(one_col_dic)
    old_list = list()  # 参考年月的工资记录
    for i in staff_id_list:
        one_staff = dict()
        one_staff['id_card'] = i.id_card
        one_staff['name'] = i.name
        for j in item_id_list:
            money = 0
            if models.Payroll.objects.filter(staff=i, item=j, give_time=refer_time).exists():
                money = models.Payroll.objects.get(staff=i, item=j, give_time=refer_time).money
            one_staff[i] = money
        old_list.append(one_staff)
    new_list = list()
    for i in staff_id_list:  # 目标年月的工资记录
        one_staff = dict()
        one_staff['id_card'] = i.id_card
        one_staff['name'] = i.name
        for j in item_id_list:
            money = 0
            if models.Payroll.objects.filter(staff=i, item=j, give_time=give_time).exists():
                money = models.Payroll.objects.get(staff=i, item=j, give_time=refer_time).money
            one_staff[i] = money
        new_list.append(one_staff)
    data_dic = dict()
    data_dic['old'] = {'each_row': old_list, 'cols_list': cols_list}
    data_dic['new'] = {'each_row': new_list, 'cols_list': cols_list}
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '审核记录两个月对比结果查询成功', 'data': data_dic}),
                        content_type='application/json')


# 工资记录确认发放前才可以通过审核
def agree_payroll_verify(request):  # 通过审核
    form = forms.EditPayrollVerify(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.WaitVerify.objects.filter(id=form.cleaned_data['id']).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '申请审批的工资记录不存在', 'data': []}),
                                      content_type='application/json')
    if models.WaitVerify.objects.filter(id=form.cleaned_data['id'], verify=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '已经审核通过', 'data': []}),
                                      content_type='application/json')
    give_time = models.WaitVerify.objects.get(id=form.cleaned_data['id']).give_time
    libs.check_payroll_records(give_time)  # 看看发放记录出来没
    payroll_obj = models.WaitVerify.objects.get(id=form.cleaned_data['id'])
    payroll_obj.verify = 1
    payroll_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '通过申请审批工资记录成功', 'data': []}),
                        content_type='application/json')


def disagree_payroll_verify(request):  # 审核拒绝
    form = forms.EditPayrollVerify(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.WaitVerify.objects.filter(id=form.cleaned_data['id']).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '申请审批的工资记录不存在', 'data': []}),
                                      content_type='application/json')
    give_time = models.WaitVerify.objects.get(id=form.cleaned_data['id']).give_time
    libs.check_payroll_records(give_time)  # 看看发放记录出来没
    payroll_obj = models.WaitVerify.objects.get(id=form.cleaned_data['id'])
    payroll_obj.verify = 2
    payroll_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '拒绝申请审批工资记录成功', 'data': []}),
                        content_type='application/json')


def freash_payroll_records(request):  # 更新工资发放记录
    form = forms.FreashPayroll(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    libs.check_payroll_records(form.cleaned_data['give_time'])
    libs.freash_payroll_records(form.cleaned_data['give_time'])
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '更新工资发放记录成功', 'data': []}),
                        content_type='application/json')


def all_payroll_records(request):
    ret = models.PayrollRecords.objects.all()
    json_dict = dict()
    data_list = list()
    for i in ret:
        data_dict = dict()
        data_dict["id"] = i.id
        data_dict["give_time"] = i.year_month
        data_dict["final_salary"] = i.final_salary
        data_dict["pay_date"] = i.pay_date
        data_dict["status"] = i.get_status_display()
        data_list.append(data_dict)
    json_dict["code"] = "ok"
    json_dict["msg"] = "查询工资记录成功"
    json_dict["data"] = data_list
    return HttpResponse(json.dumps(json_dict), content_type='application/json')


def confirm_payroll_records(request):
    form = forms.ConfirmPayroll(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.PayrollRecords.objects.filter(id=form.cleaned_data['id']).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '该年月工资发放记录不存在', 'data': []}),
                                      content_type='application/json')
    payroll_obj = models.PayrollRecords.objects.get(give_time=form.cleaned_data['give_time'])
    payroll_obj.pay_date = form.cleaned_data['pay_date']
    payroll_obj.status = 1
    payroll_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '确认工资发放记录成功', 'data': []}),
                        content_type='application/json')


# 查询某员工某年月工资条目记录
def one_payroll(request):
    form = forms.OnePayroll(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    staff_id = form.cleaned_data['staff_id']
    give_time = form.cleaned_data['give_time']
    item_set = basic_models.ItemUser.objects.filter(user=request.user)  # 查出用户当前有权限查看的条目
    item_list = list()
    for i in item_set:
        item_list.append(i.item_id)
    # 得出可以对用户展示的工资记录
    if not basic_models.Staff.objects.filter(id=staff_id, status=1).exists():
        return HttpResponse(json.dumps({'code': 'ok', 'msg': '员工无效', 'data': []}),
                            content_type='application/json')
    payroll_list = list(models.Payroll.objects.filter(staff_id=staff_id, give_time=give_time, item_id__in=item_list).
                        values('item__id', 'item__name', 'money'))
    data_list = [{"label": "员工id", "prop": "staff_id", "value": staff_id, "isedit": False}]
    for i in payroll_list:  # 因为只有一个员工，列定义和一行记录放在一个循环写入
        data_list.append({"label": i["item__name"], "prop": str(i["item__id"]), "value": i["money"], "isedit": True})
    return HttpResponse(
        json.dumps({'code': 'ok', 'msg': '查询员工某年月工资记录成功', 'data': data_list}),
        content_type='application/json')


# 编辑单条员工工资记录
def edit_one_payroll(request):
    form = forms.EditOnePayroll(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    staff_id = form.cleaned_data['staff_id']
    give_time = form.cleaned_data['give_time']
    libs.check_verify(give_time, request.user)  # 检查审核状态
    libs.check_payroll_records(give_time)  # 检查该年月工资发放状态
    item_u = form.cleaned_data['items']
    item_dic = json.loads(item_u)
    item_id_list = list(item_dic.keys())
    item_set = basic_models.ItemUser.objects.filter(user=request.user)  # 查出用户当前有权限查看的条目
    item_list = list()
    for i in item_set:
        item_list.append(i.item_id)  # 得出可以对用户展示的工资记录
    for i in item_id_list:  # 用户因为权限查询不到这条条目记录，请求编辑也不会出现，正常不出现
        if int(i) not in item_list:
            return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '用户权限不可以处理这些条目', 'data': []}),
                                          content_type='application/json')
    try:
        with transaction.atomic():  # 原子操作
            for i in item_id_list:
                # 正常不出现这种情况
                if not models.Payroll.objects.filter(staff_id=staff_id, item_id=int(i), give_time=give_time).exists():
                    return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '编辑的工资记录不存在', 'data': []}),
                                                  content_type='application/json')
                models.Payroll.objects.filter(staff_id=staff_id, item_id=int(i), give_time=give_time).update(
                    money=item_dic[i])
            return HttpResponse(
                json.dumps({'code': 'ok', 'msg': '编辑员工工资记录成功', 'data': []}),
                content_type='application/json')
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')


def one_teach_payroll(request):
    form = forms.OneTeachPayroll(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    staff_id = form.cleaned_data['staff_id']
    item_ch = form.cleaned_data['item_ch']  # 要查看的条目的id，权限处理
    give_time = form.cleaned_data['give_time']
    item_set = basic_models.ItemUser.objects.filter(user=request.user)  # 查出用户当前有权限查看的有效条目
    item_list = list()
    for i in item_set:
        item_list.append(i.item.name)  # 得出可以对用户展示的工资条目的名字
    if item_ch not in item_list:
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '用户权限不可以查看该条目的细项', 'data': []}),
                                      content_type='application/json')
    time_teachitem = models.TeachRoll.objects.filter(staff_id=staff_id, give_time=give_time, item__item__name=item_ch,
                                                     item__type=0)
    notime_teachitem = models.TeachRoll.objects.filter(staff_id=staff_id, give_time=give_time, item__item__name=item_ch,
                                                       item__type=1)
    basic_list = [{"label": "员工id", "prop": "staff_id", "value": staff_id, "isedit": False}]
    time_list = list()
    notime_list = list()
    for i in time_teachitem:
        time_list.append({"label": i.item.name, "prop": str(i.item.id), "value": i.teach_time, "isedit": True})
    for i in notime_teachitem:
        notime_list.append({"label": i.item.name, "prop": str(i.item_id), "value": i.money, "isedit": True})
    return HttpResponse(
        json.dumps({'code': 'ok', 'msg': '查询员工某年月工资记录成功',
                    'data': {"basic_list": basic_list, "time_list": time_list, "notime_list": notime_list}}),
        content_type='application/json')


def edit_one_teach_payroll(request):
    form = forms.EditTeachPayroll(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    staff_id = form.cleaned_data['staff_id']
    give_time = form.cleaned_data['give_time']
    time_items = form.cleaned_data['time_items']
    item_ch = form.cleaned_data['item_ch']
    if not basic_models.Item.objects.filter(name=item_ch, status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '三项条目无效', 'data': []}),
                                      content_type='application/json')
    item_obj = basic_models.Item.objects.get(name=item_ch, status=1)
    if not basic_models.ItemUser.objects.filter(user=request.user, item=item_obj):
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '用户权限不可以查看三项条目的细项', 'data': []}),
                                      content_type='application/json')
    notime_items = form.cleaned_data['notime_items']
    time_dic = json.loads(time_items)  # 这些细项所属条目需要检查用户是否有该条目权限
    notime_dic = json.loads(notime_items)  # 这些细项所属条目需要检查用户是否有该条目权限，后期检查
    time_id_list = list(time_dic.keys())
    notime_id_list = list(notime_dic.keys())
    try:
        with transaction.atomic():  # 原子操作
            teachitem_payroll = 0
            for i in time_id_list:  # 计课时细项
                if not models.TeachRoll.objects.filter(staff_id=staff_id, item_id=int(i), give_time=give_time).exists():
                    return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '编辑的计课时细项记录不存在', 'data': []}),
                                                  content_type='application/json')
                if basic_models.UnitPrice.objects.filter(course_id=int(i), staff_id=staff_id).exists():
                    teachitem_price = basic_models.UnitPrice.objects.get(course_id=i, staff_id=staff_id).price
                else:
                    teachitem_price = 0  # 得出员工这个计时细项的单价
                teach_time = time_dic[i]
                money = teachitem_price * teach_time
                teachitem_payroll += money  # 累加细项的工资
                models.TeachRoll.objects.filter(staff_id=staff_id, item_id=int(i), give_time=give_time).update(
                    teach_time=teach_time, the_price=teachitem_price, money=money)
            for i in notime_id_list:  # 非计课时细项
                if not models.TeachRoll.objects.filter(staff_id=staff_id, item_id=int(i), give_time=give_time).exists():
                    return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '编辑的非计算课时细项记录不存在', 'data': []}),
                                                  content_type='application/json')
                teachitem_payroll += notime_dic[i]  # 累加细项的工资
                models.TeachRoll.objects.filter(staff_id=staff_id, item_id=i, give_time=give_time).update(
                    money=notime_dic[i])
            # 处理这个员工这堆细项的条目
            if not models.WaitVerify.objects.filter(work_user=request.user, give_time=give_time).exists():
                models.WaitVerify.objects.create(work_user=request.user, give_time=give_time)  # 创建暂存工资审核记录
            wait_verify_obj = models.WaitVerify.objects.get(work_user=request.user, give_time=give_time)
            if not models.Payroll.objects.filter(staff_id=staff_id, item=item_obj).exists():
                models.Payroll.objects.create(staff_id=staff_id, item=item_obj, money=teachitem_payroll,
                                              give_time=give_time,
                                              verify=wait_verify_obj)
            else:
                item_payroll_obj = models.Payroll.objects.get(staff_id=staff_id, item=item_obj)
                item_payroll_obj.money = teachitem_payroll
                item_payroll_obj.save()
            return HttpResponse(
                json.dumps({'code': 'ok', 'msg': '编辑员工细项目记录成功', 'data': []}),
                content_type='application/json')
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
