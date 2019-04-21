# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
import datetime
import json
import random
import string
import urllib2
from io import BytesIO

import requests
import xlrd
import xlwt
from django.db import transaction  # 原子操作
from django.http import FileResponse
from django.http import HttpResponse, HttpResponseBadRequest
from qiniu import Auth
from qiniu.utils import urlsafe_base64_encode

from basic import models, forms
from sh_salary.settings import QINIU


# Create your views here.
def add_department(request):
    form = forms.AddDepartment(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if models.Department.objects.filter(name=form.cleaned_data['name'], status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要添加的部门已存在', 'data': []}),
                                      content_type='application/json')
    # 已删部门额外管理,无形中添改感觉不好
    # if models.Department.objects.filter(name=form.cleaned_data['name'], status=0).exists():
    #     department_obj = models.Department.objects.get(name=form.cleaned_data['name'])
    #     department_obj.remark = form.cleaned_data['remark']
    #     department_obj.status = 1
    models.Department.objects.create(name=form.cleaned_data['name'], remark=form.cleaned_data['remark'])
    return HttpResponse(json.dumps({'code': 'ok', 'data': [], 'msg': '添加部门成功'}),
                        content_type='application/json')


def edit_department(request):
    form = forms.EditDepartment(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.Department.objects.filter(id=form.cleaned_data['id'], status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要编辑的部门不存在', 'data': []}),
                                      content_type='application/json')
    # 情境：添加一个部门，如果名字已经在有效部门存在，则不允许添加，如果在已删除部门存在，则不管，允许添加
    # 已删除部门需要专门额外去管理
    if models.Department.objects.filter(name=form.cleaned_data['name'], status=1).exclude(
            id=form.cleaned_data['id']).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '编辑后的部门的名字已存在', 'data': []}),
                                      content_type='application/json')
    department_obj = models.Department.objects.get(id=form.cleaned_data['id'])
    department_obj.name = form.cleaned_data['name']
    department_obj.remark = form.cleaned_data['remark']
    department_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'data': [], 'msg': '编辑部门成功'}),
                        content_type='application/json')


def del_department(request):
    form = forms.DelDepartment(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')

    if not models.Department.objects.filter(id=form.cleaned_data['id'], status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要删除的部门不存在', 'data': []}),
                                      content_type='application/json')
    department_obj = models.Department.objects.get(id=form.cleaned_data['id'])
    department_obj.status = 0
    department_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'data': [], 'msg': '删除部门成功'}),
                        content_type='application/json')


def one_department(request):
    form = forms.DelDepartment(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    department_id = form.cleaned_data['id']
    if not models.Department.objects.filter(id=department_id).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'data': [], 'msg': '查询部门无效'}),
                                      content_type='application/json')
    department_obj = models.Department.objects.get(id=department_id)
    department_dic = dict()
    department_dic['id'] = department_obj.id
    department_dic['name'] = department_obj.name
    department_dic['remark'] = department_obj.remark
    return HttpResponse(json.dumps({'code': 'ok', 'data': department_dic, 'msg': '查询部门成功'}),
                        content_type='application/json')


def all_department(request):
    query_set = models.Department.objects.all()
    json_dic = dict()
    json_dic['code'] = 'ok'
    json_dic['mag'] = '查询所有部门成功'
    data_list = list()
    for i in query_set:
        one_department = dict()
        one_department['id'] = i.id
        one_department['name'] = i.name
        one_department['remark'] = i.remark
        data_list.append(one_department)
    json_dic['data'] = data_list
    return HttpResponse(json.dumps(json_dic), content_type='application/json')


# 添加一个员工时，给员工自动加上课时细项管理
def add_staff(request):
    form = forms.AddStaff(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if models.Staff.objects.filter(id_card=form.cleaned_data['id_card'], status=1).exists():  # 保证身份证唯一
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要添加的员工已存在', 'data': []}),
                                      content_type='application/json')
    if not models.Department.objects.filter(id=form.cleaned_data['department'], status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要添加的员工的部门不存在', 'data': []}),
                                      content_type='application/json')
    if models.Staff.objects.filter(id_card=form.cleaned_data['id_card'], status=0).exists():
        staff_obj = models.Staff.objects.get(id_card=form.cleaned_data['id_card'])
        staff_obj.name = form.cleaned_data['name']
        staff_obj.phone = form.cleaned_data['phone']
        staff_obj.department = models.Department.objects.get(id=form.cleaned_data['department'])
        staff_obj.bank_card_num = form.cleaned_data['bank_card_num']
        staff_obj.bank_name = form.cleaned_data['bank_name']
        staff_obj.entry_date = datetime.datetime.strptime(form.cleaned_data['entry_date'], '%Y-%m-%d')
        staff_obj.tax_start = form.cleaned_data['tax_start']
        staff_obj.remark = form.cleaned_data['remark']
        staff_obj.status = 1
        staff_obj.save()
    else:
        staff_obj = models.Staff()
        staff_obj.id_card = form.cleaned_data['id_card']
        staff_obj.name = form.cleaned_data['name']
        staff_obj.phone = form.cleaned_data['phone']
        staff_obj.department = models.Department.objects.get(id=form.cleaned_data['department'])
        staff_obj.bank_card_num = form.cleaned_data['bank_card_num']
        staff_obj.bank_name = form.cleaned_data['bank_name']
        staff_obj.entry_date = datetime.datetime.strptime(form.cleaned_data['entry_date'], '%Y-%m-%d')
        staff_obj.tax_start = form.cleaned_data['tax_start']
        staff_obj.remark = form.cleaned_data['remark']
        staff_obj.save()

    # 给该员工按默认单价生成计课时单价记录
    for i in models.TeachItem.objects.filter(type=0):
        models.UnitPrice.objects.create(course=i, staff=staff_obj, price=i.default_price)

    return HttpResponse(json.dumps({'code': 'ok', 'data': [], 'msg': '添加员工成功并初始化教学课时费'}),
                        content_type='application/json')


def edit_staff(request):
    form = forms.EditStaff(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.Staff.objects.filter(id=form.cleaned_data['id'], department__status=1, status=1):
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要编辑的员工无效', 'data': []}),
                                      content_type='application/sjon')
    if not models.Department.objects.filter(id=form.cleaned_data['department'], status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '编辑员工的部门不存在', 'data': []}),
                                      content_type='applicatin/json')
    staff_obj = models.Staff.objects.get(id=form.cleaned_data['id'])
    staff_obj.id_card = form.cleaned_data['id_card']
    if models.Staff.objects.filter(id_card=form.cleaned_data['id_card']).exclude(id=form.cleaned_data['id']):
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '编辑后的身份证和其他人冲突', 'data': []}),
                                      content_type='applicatin/json')
    staff_obj.name = form.cleaned_data['name']
    staff_obj.phone = form.cleaned_data['phone']
    staff_obj.department = models.Department.objects.get(id=form.cleaned_data['department'])
    # 部门改动
    staff_obj.bank_card_num = form.cleaned_data['bank_card_num']
    staff_obj.bank_name = form.cleaned_data['bank_name']
    staff_obj.entry_date = datetime.datetime.strptime(form.cleaned_data['entry_date'], '%Y-%m-%d')
    staff_obj.tax_start = form.cleaned_data['tax_start']
    staff_obj.remark = form.cleaned_data['remark']
    staff_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '编辑员工成功', 'data': []}), content_type='application/json')


def del_staff(request):
    form = forms.DelStaff(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.Staff.objects.filter(id=form.cleaned_data['id'], status=1):
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要删除的员工无效', 'data': []}))
    staff_obj = models.Staff.objects.get(id=form.cleaned_data['id'])
    staff_obj.status = 0
    staff_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '删除员工成功', 'data': []}), content_type='application/json')


def all_staff(request):
    json_dic = dict()
    json_dic['code'] = 'ok'
    json_dic['msg'] = '查询所有员工成功'
    data_list = list()
    query_set = models.Staff.objects.select_related('department').filter(status=1, department__status=1)
    for i in query_set:
        one_staff = dict()
        one_staff['id'] = i.id
        one_staff['id_card'] = i.id_card
        one_staff['name'] = i.name
        one_staff['phone'] = i.phone
        one_staff['department'] = i.department.name
        one_staff['bank_card_num'] = i.bank_card_num
        one_staff['bank_name'] = i.bank_name
        one_staff['entry_date'] = i.entry_date.strftime('%Y-%m-%d')
        one_staff['tax_start'] = i.tax_start
        one_staff['remark'] = i.remark
        data_list.append(one_staff)
    json_dic['data'] = data_list
    return HttpResponse(json.dumps(json_dic), content_type='application/json')


def one_staff(request):
    form = forms.OneStaff(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    staff_id = form.cleaned_data['id']
    if not models.Staff.objects.filter(id=staff_id, status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '查询的员工无效', 'data': []}),
                                      content_type='application/json')
    staff_obj = models.Staff.objects.get(id=staff_id, status=1)
    data_dic = dict()
    data_dic['id'] = staff_obj.id
    data_dic['name'] = staff_obj.name
    data_dic['id_card'] = staff_obj.id_card
    data_dic['phone'] = staff_obj.phone
    data_dic['department'] = staff_obj.department.id
    data_dic['department_ch'] = staff_obj.department.name
    data_dic['bank_card_num'] = staff_obj.bank_card_num
    data_dic['bank_name'] = staff_obj.bank_name
    data_dic['entry_date'] = staff_obj.entry_date.strftime('%Y-%m-%d')
    data_dic['tax_start'] = staff_obj.tax_start
    data_dic['remark'] = staff_obj.remark
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '查询单个员工成功', 'data': data_dic}),
                        content_type='application/json')


# 上传自命名文档
def upload_staff_file(request):
    form = forms.UploadStafffile(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    q = Auth(QINIU['access_key'], QINIU['secret_key'])
    file_name = form.cleaned_data['name']  # 用户给的名字
    staff_id = form.cleaned_data['staff']
    remark = form.cleaned_data['remark']
    data_file = request.FILES.get('file')  # 不会form校验文件
    data_file_lastname = request.FILES.get('file').name.split('.')[-1]
    if not models.Staff.objects.filter(id=staff_id).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '上传文件的员工不存在', 'data': []}),
                                      content_type='application/json')
    key = ''.join(random.sample(string.ascii_letters + string.digits, 8))  # 随机八位字符
    while models.File.objects.filter(qiniu_name=key):  # 假如随机的八位字符已经被使用
        key = ''.join(random.sample(string.ascii_letters + string.digits, 8))  # 新随机八位字符
    token = q.upload_token(QINIU['bucket_name'], key, 3600)
    base64_file = base64.b64encode(data_file.read())
    qiniu_upload_url = "http://up-z2.qiniu.com/putb64/%s/key/%s/mimeType/%s" % \
                       (str(-1), urlsafe_base64_encode(key + '.' + data_file_lastname),
                        urlsafe_base64_encode(data_file_lastname))
    headers = {"Content-type": "application/octet-stream", "Authorization": "UpToken " + token}
    requests.post(qiniu_upload_url, headers=headers, data=base64_file)
    # resp = json.loads(requests.post(qiniu_upload_url, headers=headers, data=base64_file).content)
    # hash = resp['hash']   # hash校验
    # filename = resp['key']
    file_obj = models.File()
    file_obj.name = file_name + '.' + data_file_lastname
    file_obj.staff = models.Staff.objects.get(id=staff_id)
    file_obj.qiniu_name = key + '.' + data_file_lastname
    file_obj.remark = remark
    file_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '上传文档成功', 'data': []}), content_type='application/json')


# 查看某员工所有自命名文档
def staff_all_file(request):
    form = forms.StaffAllfile(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    staff_id = form.cleaned_data['id']
    if not models.Staff.objects.filter(id=staff_id).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '员工不存在', 'data': []}),
                                      content_type='application/json')
    query_set = models.File.objects.filter(staff_id=form.cleaned_data['id'])
    data_list = list()
    for i in query_set:
        one_file_dic = dict()
        one_file_dic['name'] = i.name
        one_file_dic['qiniu_name'] = i.qiniu_name
        one_file_dic['remark'] = i.remark
        data_list.append(one_file_dic)
    json_dic = {'code': 'ok', 'data': data_list, 'msg': '查询员工所有文档成功'}
    return HttpResponse(json.dumps(json_dic), content_type='application/json')


def download_staff_file(request):
    form = forms.DownloadStafffile(request.GET)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    q = Auth(QINIU['access_key'], QINIU['secret_key'])
    qiniu_name = form.cleaned_data['qiniu_name']
    url = QINIU['domain'] + '/{}?attname='.format(qiniu_name)
    private_url = q.private_download_url(url, expires=300)  # 得到文件资源的URL
    # 一、直接FileResponse，可行
    file_obj = urllib2.urlopen(private_url)
    # file_data = base64.b64encode(file_obj.read())
    file_data = file_obj.read()
    return FileResponse(file_data)
    # 二、用HttpResponse
    # response = HttpResponse(content_type='APPLICATION/OCTET-STREAM')
    # response.write(file_data)
    # return response
    # 二、另一种形式
    # return HttpResponse(file_data, content_type='APPLICATION/OCTET-STREAM')
    # 三、仿导出Excel的操作
    # output = StringIO.StringIO()
    # output.write(file_data)
    # file_data.save(output)
    # output.seek(0)
    # response.write(output.getvalue())
    # return response
    # 四、直接重定向
    # return redirect(private_url)


def export_staff(request):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = u'attachment;filename=员工模板.xls'
    wb = xlwt.Workbook(encoding='utf8')
    # 样式
    style1 = xlwt.easyxf('font: height 220, name SimSun, colour_index black, '
                         'bold off; align: wrap on, vert centre, '
                         'horiz left;border:left thin, right thin, top thin, bottom thin')
    style2 = xlwt.easyxf('font: height 320, name SimSun, colour_index black, '
                         'bold off; align: wrap on, vert centre, '
                         'horiz center;border:left thin, right thin, top thin, bottom thin')
    sheet = wb.add_sheet(u'员工资料', cell_overwrite_ok=True)

    sheet.write_merge(0, 0, 0, 9, u'深圳市光明新区精华学校', style2)
    sheet.write_merge(1, 1, 0, 0, u'序号', style1)
    sheet.write_merge(1, 1, 1, 1, u'姓名', style1)
    sheet.write_merge(1, 1, 2, 2, u'手机号', style1)
    sheet.write_merge(1, 1, 3, 3, u'身份证号', style1)
    sheet.write_merge(1, 1, 4, 4, u'银行卡号', style1)
    sheet.write_merge(1, 1, 5, 5, u'支付银行', style1)
    sheet.write_merge(1, 1, 6, 6, u'个税起征点', style1)
    sheet.write_merge(1, 1, 7, 7, u'部门', style1)
    sheet.write_merge(1, 1, 8, 8, u'入职年月日', style1)
    sheet.write_merge(1, 1, 9, 9, u'备注', style1)
    for i in range(100):
        sheet.row(i).set_style(xlwt.easyxf('font:height 360'))
    for i in range(3, 13):
        sheet.write(i, 0, i - 2, style1)
        for j in range(1, 10):
            if j == 3 or j == 4:
                sheet.write(i, j, "'", style1)
            else:
                sheet.write(i, j, '', style1)
    sheet.write(2, 0, '上传时请删除此行和空行', style1)
    sheet.write(2, 1, '例如:张三', style1)
    sheet.write(2, 2, '13800138000', style1)
    sheet.write(2, 3, '440881000000000000', style1)
    sheet.write(2, 4, '132546879879564132', style1)
    sheet.write(2, 5, '中国银行', style1)
    sheet.write(2, 6, '5000', style1)
    sheet.write(2, 7, '小学部', style1)
    sheet.write(2, 8, '2019-1-1', style1)
    sheet.write(2, 9, '对员工的备注', style1)
    sheet.col(0).width = 256 * 10
    sheet.col(1).width = 256 * 15
    sheet.col(2).width = 256 * 20
    sheet.col(3).width = 256 * 30
    sheet.col(4).width = 256 * 30
    sheet.col(5).width = 256 * 15
    sheet.col(6).width = 256 * 15
    sheet.col(7).width = 256 * 15
    sheet.col(8).width = 256 * 15
    sheet.col(9).width = 256 * 30

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response.write(output.getvalue())
    return response


def upload_staff(request):
    try:
        work_book = xlrd.open_workbook(filename=None, file_contents=request.FILES['data'].read())
        sheet = work_book.sheet_by_index(0)
        col_name_list = ['name', 'phone', 'id_card', 'bank_card_num', 'bank_name', 'tax_start', 'deaprtment',
                         'entry_date', 'remark']
        each_row = list()
        for row in range(2, sheet.nrows):  # 设第二行开始数据
            value_list = list()  # 存excel每行数据，匹配取出
            for col in range(0, sheet.ncols):
                one_value = sheet.cell(row, col).value
                if not one_value:
                    one_value = 'null'
                value_list.append(one_value)
            each_row.append(dict(zip(col_name_list, value_list)))
        cols_list = [{'prop': 'name', 'label': '姓名'}, {'prop': 'id_card', 'label': '身份证'},
                     {'prop': 'id_card', 'label': '身份证'}, {'prop': 'bank_card_num', 'label': '银行卡号码'},
                     {'prop': 'bank_name', 'label': '银行名字'}, {'prop': 'tax_start', 'label': '个税起征点'},
                     {'prop': 'deaprtment', 'label': '部门'}, {'prop': 'entry_date', 'label': '入职年月日'},
                     {'prop': 'remark', 'label': '备注'}]
        json_dic = dict()
        json_dic["code"] = "ok"
        json_dic["msg"] = "员工资料表解析成功"
        json_dic["data"] = {'each_row': each_row, 'cols_list': cols_list}
        return HttpResponse(json.dumps(json_dic), content_type="application/json")
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '解析员工资料表失败:' + e.message, 'data': []}
                                                 , content_type="application/json"))


def import_staff(request):  # 给解析工资表调用，上传单条员工资料
    form = forms.ImportStaff(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    name = form.cleaned_data['name']
    phone = form.cleaned_data['phone']
    id_card = form.cleaned_data['id_card']
    if models.Staff.objects.filter(id_card=id_card).exists():
        return HttpResponseBadRequest(
            json.dumps({'code': 'false', 'msg': '身份证代表的员工已经存在', 'data': []},
                       content_type="application/json"))
    bank_card_num = form.cleaned_data['bank_card_num']
    bank_name = form.cleaned_data['bank_name']
    tax_start = form.cleaned_data['tax_start']
    if not models.Department.objects.filter(name=form.cleaned_data['department']).exists():
        return HttpResponseBadRequest(
            json.dumps({'code': 'false', 'msg': '部门无效', 'data': []}, content_type="application/json"))
    department_obj = models.Department.objects.get(name=form.cleaned_data['department'])
    entry_date = form.cleaned_data['entry_date'].strptime('%Y-%m-%d')
    remark = form.cleaned_data['remark']
    models.Staff.objects.create(id_card=id_card, name=name, phone=phone, bank_card_num=bank_card_num,
                                bank_name=bank_name,
                                entry_date=entry_date, tax_start=tax_start, department=department_obj, remark=remark)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '上传一条员工记录成功', 'data': []}),
                        content_type='application/json')


# 为了让工资记录和课时记录(和为教学工资的教学加班、安全补助、德育补助）不产生冲突，新建课时记录模型
def add_item(request):
    form = forms.AddItem(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    type = {"应扣": 0, "应发": 1}[form.cleaned_data['type']]
    sec_type = {"应扣": 0, "标准工资": 1, "教学工资": 2, "其他工资": 3}.get(form.cleaned_data['sec_type'])
    if models.Item.objects.filter(type=type, sec_type=sec_type, name=form.cleaned_data['name'],
                                  status=1).exists():  # 存在看得见的有效
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '该条目已存在', 'data': []}),
                                      content_type='application/json')
    # 不要这种暗自添改
    # if models.Item.objects.filter(type=type, sec_type=sec_type, name=form.cleaned_data['name'], status=0).exists():
    #     item_obj = models.Item.objects.get(name=form.cleaned_data['name'], status=0)
    #     item_obj.type = type
    #     item_obj.sec_type = sec_type
    #     item_obj.name = form.cleaned_data['name']
    #     item_obj.remark = form.cleaned_data['remark']
    #     item_obj.save()
    else:
        models.Item.objects.create(type=type, sec_type=sec_type, name=form.cleaned_data['name'],
                                   remark=form.cleaned_data['remark'])
        return HttpResponse(json.dumps({'code': 'ok', 'msg': '添加条目成功', 'data': []}),
                            content_type='application/json')


def one_item(request):
    form = forms.OneItem(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    item_id = form.cleaned_data['id']
    if not models.Item.objects.filter(id=item_id, status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'mag': '要编辑的条目不存在', 'data': []}),
                                      content_type='application/json')
    item_obj = models.Item.objects.get(id=item_id, status=1)
    item_dic = {'id': item_obj.id, 'type': item_obj.get_type_display(), 'sec_type': item_obj.get_sec_type_display(),
                'name': item_obj.name, 'remark': item_obj.remark}
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '查单条条目成功', 'data': item_dic}),
                        content_type='application/json')


def edit_item(request):
    form = forms.EditItem(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.Item.objects.filter(id=form.cleaned_data['id'], status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'mag': '要编辑的条目不存在', 'data': []}),
                                      content_type='application/json')
    item_obj = models.Item.objects.get(id=form.cleaned_data['id'])
    item_obj.type = {"应扣": 0, "应发": 1}.get(form.cleaned_data['type'])
    item_obj.sec_type = {"应扣": 0, "标准工资": 1, "教学工资": 2,
                         "其他工资": 3, "三项": 4}.get(form.cleaned_data['sec_type'])
    item_obj.name = form.cleaned_data['name']
    item_obj.remark = form.cleaned_data['remark']
    item_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '编辑条目成功', 'data': []}), content_type='application/json')


def del_item(request):
    form = forms.DelItem(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.Item.objects.filter(id=form.cleaned_data['id'], status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'mag': '要删除的条目不存在', 'data': []}),
                                      content_type='application/json')
    item_obj = models.Item.objects.get(id=form.cleaned_data['id'])
    item_obj.status = 0
    item_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '删除条目成功', 'data': []}), content_type='application/json')


def all_item(request):
    query_set = models.Item.objects.filter(status=1)
    data_list = list()
    for i in query_set:
        one_item_dict = dict()
        one_item_dict['id'] = i.id
        one_item_dict['type'] = i.get_type_display()
        one_item_dict['sec_type'] = i.get_sec_type_display()
        one_item_dict['name'] = i.name
        one_item_dict['remark'] = i.remark
        data_list.append(one_item_dict)
    json_data = {'code': 'ok', 'msg': '查询条目成功', 'data': data_list}
    return HttpResponse(json.dumps(json_data), content_type='application/json')


def all_user(request):
    user_set = models.User.objects.all()
    user_list = list()
    for i in user_set:
        one_user = dict()
        one_user['id'] = i.id
        one_user['username'] = i.username
        one_user['first_name'] = i.first_name
        one_user['is_superuser'] = i.is_superuser
        user_list.append(one_user)
    return HttpResponse(json.dumps({'code': 'ok', 'data': user_list, 'msg': '查询所有用户成功'}),
                        content_type='application/json')


# 以用户id去查
def all_item_user(request):
    form = forms.AllItemUser(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    query_set = models.ItemUser.objects.select_related('item').filter(user=form.cleaned_data['id'], item__status=1)
    data_list = list()
    for i in query_set:
        one_user = dict()
        one_user['item_id'] = i.item_id
        one_user['item_name'] = i.item.name
        data_list.append(one_user)
    return HttpResponse(json.dumps({'code': 'ok', 'data': data_list, 'msg': '查询用户管理的条目成功'}),
                        content_type='application/json')


# 查询登陆用户所能管理的条目
def all_item_owner(request):
    agree_item = ['教学加班', '德育补助', '安全补助']
    query_set = models.ItemUser.objects.select_related('item').filter(user=request.user, item__status=1). \
        exclude(item__name__in=agree_item)
    data_list = list()
    for i in query_set:
        one_user = dict()
        one_user['item_id'] = i.item_id
        one_user['item_name'] = i.item.name
        data_list.append(one_user)
    return HttpResponse(json.dumps({'code': 'ok', 'data': data_list, 'msg': '查询用户管理的条目成功'}),
                        content_type='application/json')


def refresh_item_user(request):
    form = forms.RefreshItemUser(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.User.objects.filter(id=form.cleaned_data['user_id']).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '处理条目的用户不存在', 'data': []}),
                                      content_type='application/json')
    try:
        with transaction.atomic():  # 原子操作
            models.ItemUser.objects.filter(user=form.cleaned_data['user_id']).delete()  # 真删
            item_id_list = form.cleaned_data['item_id_str'].split('|')
            for i in item_id_list:
                if not models.Item.objects.filter(id=i).exists():
                    return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要给用户添加的条目不存在', 'data': []}),
                                                  content_type='application/json')
                item_obj = models.Item.objects.get(id=i)
                user_obj = models.User.objects.get(id=form.cleaned_data['user_id'])
                models.ItemUser.objects.create(item=item_obj, user=user_obj)
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'code': 'ok', 'msg': e, 'data': []}),
                                      content_type='application/json')
    return HttpResponse(json.dumps({'code': 'ok', 'data': [], 'msg': '对用户刷新管理条目成功'}),
                        content_type='application/json')


# 对教学条目细项进行管理
# 每添加一个[教学]计课时细项，要给对应部门所有员工自动创建课时费记录
def add_teachitem(request):
    form = forms.AddTeachitem(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.Item.objects.filter(id=form.cleaned_data['id'], status=1):
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '工资条目不存在', 'data': []}),
                                      content_type='application/json')
    item_obj = models.Item.objects.get(id=form.cleaned_data['id'])
    type = form.cleaned_data['type']
    name = form.cleaned_data['name']
    default_price = form.cleaned_data['default_price']
    remark = form.cleaned_data['remark']
    # 对有效的进行变动，状态为软删了的不进行管理，另外进行管理
    if models.TeachItem.objects.filter(item=item_obj, type=type, name=name, status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '该教学细项已存在', 'data': []}),
                                      content_type='application/json')
    # 被删的另外管理，不自动添改了
    # if models.TeachItem.objects.filter(item=item_obj, type=type, name=name, status=0).exists():
    #     teachitem_obj = models.TeachItem.objects.get(item=item_obj, type=type, name=name, status=0)
    #     teachitem_obj.status = 1
    #     teachitem_obj.default_price = default_price
    #     teachitem_obj.remark = remark
    #     teachitem_obj.save()
    else:
        teachitem_obj = models.TeachItem()
        teachitem_obj.item = item_obj
        teachitem_obj.type = type
        teachitem_obj.name = name
        teachitem_obj.default_price = default_price
        teachitem_obj.remark = remark
        teachitem_obj.save()
        # 0代表这是新建条目的细项，要对计课时条目给所有员工要生成课时费记录
        if type == "0":
            for i in models.Staff.objects.all():  # 不管员工有无效，都保持最新课时费记录
                models.UnitPrice.objects.create(course=teachitem_obj, staff=i, price=default_price)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '添加教学条目成功', 'data': []}),
                        content_type='application/json')


def one_teachitem(request):
    form = forms.OneTeachitem(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    teachitem_id = form.cleaned_data['id']
    if not models.TeachItem.objects.filter(id=teachitem_id).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'data': [], 'msg': '查询详细条目无效'}),
                                      content_type='application/json')
    teachitem_obj = models.TeachItem.objects.get(id=teachitem_id)
    teachitem_dic = dict()
    teachitem_dic['type'] = teachitem_obj.get_type_display()
    teachitem_dic['name'] = teachitem_obj.name
    teachitem_dic['default_price'] = teachitem_obj.default_price
    teachitem_dic['remark'] = teachitem_obj.remark
    return HttpResponse(json.dumps({'code': 'ok', 'data': teachitem_dic, 'msg': '查询细项成功'}),
                        content_type='application/json')


def all_teachitem(request):  # 查某个条目的所有细项
    form = forms.AllTeachitem(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.Item.objects.filter(name=form.cleaned_data['item_ch'], status=1):
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': '要管理细项的工资条目不存在', 'data': []}),
                                      content_type='application/json')
    item_obj = models.Item.objects.get(name=form.cleaned_data['item_ch'], status=1)
    query_set_time = models.TeachItem.objects.filter(item=item_obj, type=0, status=1)
    query_set_notime = models.TeachItem.objects.filter(item=item_obj, type=1, status=1)
    teach_list_time = list()  # 计课时的和不计课时
    teach_list_notime = list()
    for i in query_set_time:
        one_teachitem_dict = dict()
        one_teachitem_dict['id'] = i.id
        one_teachitem_dict['name'] = i.name
        one_teachitem_dict['default_price'] = i.default_price
        one_teachitem_dict['remark'] = i.remark
        teach_list_time.append(one_teachitem_dict)
    for i in query_set_notime:
        one_teachitem_dict = dict()
        one_teachitem_dict['id'] = i.id
        one_teachitem_dict['name'] = i.name
        one_teachitem_dict['remark'] = i.remark
        teach_list_notime.append(one_teachitem_dict)
    json_data = {'code': 'ok', 'msg': '查询教学细项成功',
                 'data': {'time': teach_list_time, 'notime': teach_list_notime}}
    return HttpResponse(json.dumps(json_data), content_type='application/json')


def edit_teachitem(request):  # 编辑细项的类别，名字和价格和备注
    form = forms.EditTeachitem(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    teach_item = form.cleaned_data['id']
    name = form.cleaned_data['name']
    type = form.cleaned_data['type']
    remark = form.cleaned_data['remark']
    default_price = form.cleaned_data['default_price']
    if not models.TeachItem.objects.filter(id=teach_item, status=1).exists():  # 删除了即使有也不给编辑，同时报条目无效
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'mag': '要编辑的教学条目无效', 'data': []}),
                                      content_type='application/json')
    models.TeachItem.objects.update(name=name, type=type, remark=remark, default_price=default_price)
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '编辑条目成功', 'data': []}), content_type='application/json')


def del_teachitem(request):
    form = forms.DelTeachitem(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    if not models.TeachItem.objects.filter(id=form.cleaned_data['id'], status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'mag': '要删除的教学条目不存在', 'data': []}),
                                      content_type='application/json')
    item_obj = models.TeachItem.objects.get(id=form.cleaned_data['id'])
    item_obj.status = 0
    item_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '删除教学细项成功', 'data': []}),
                        content_type='application/json')


def staff_courseprice(request):
    form = forms.StaffCourseprice(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    # 课时条目改动了也无影响
    if not models.Staff.objects.filter(id=form.cleaned_data['id'], status=1).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'data': [], 'msg': '查询课程课时费的员工不存在'}),
                                      content_type='application/json')
    data_list = list()
    query_set = models.UnitPrice.objects.select_related('course', 'staff').filter(staff__id=form.cleaned_data['id'])
    for i in query_set:
        one_course_dic = dict()
        one_course_dic['id'] = i.id
        one_course_dic['course'] = i.course.name
        one_course_dic['price'] = i.price
        data_list.append(one_course_dic)
    json_dic = {'code': 'ok', 'msg': '查询员工工资细项课时费成功', 'data': data_list}
    return HttpResponse(json.dumps(json_dic), content_type='application/json')


# 对某员工某课的课时细项单价,只修改单价
def one_unitprice(request):
    form = forms.OneUnitprice(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    unit_price_id = form.cleaned_data['id']
    if not models.UnitPrice.objects.filter(id=unit_price_id).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'data': [], 'msg': '员工课时记录无效'}),
                                      content_type='application/json')
    unit_price_obj = models.UnitPrice.objects.get(id=unit_price_id)
    one_dic = dict()
    one_dic['id'] = unit_price_obj.id
    one_dic['name'] = unit_price_obj.course.name
    one_dic['price'] = unit_price_obj.price
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '查询课时费记录成功', 'data': one_dic}),
                        content_type='application/json')


def edit_unitprice(request):
    form = forms.EditUnitprice(request.POST)
    if not form.is_valid():
        e = ','.join([form.errors[i][0] for i in form.errors]) if len(form.errors) > 0 else u'未知错误'
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'msg': e, 'data': []}),
                                      content_type='application/json')
    # 这个情况一般是不会不存在的
    if not models.UnitPrice.objects.filter(id=form.cleaned_data['id']).exists():
        return HttpResponseBadRequest(json.dumps({'code': 'false', 'mag': '要编辑的课时记录无效', 'data': []}),
                                      content_type='application/json')
    unitprice_obj = models.UnitPrice.objects.get(id=form.cleaned_data['id'])
    unitprice_obj.price = form.cleaned_data['price']
    unitprice_obj.save()
    return HttpResponse(json.dumps({'code': 'ok', 'msg': '编辑员工课时单价成功', 'data': []}),
                        content_type='application/json')
