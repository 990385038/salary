# -*- coding:utf-8 -*-
"""dami URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

from basic import views

urlpatterns = [
    url('^add_department$', views.add_department),  # 添加部门
    url('^edit_department$', views.edit_department),  # 编辑部门
    url('^del_department$', views.del_department),  # 删除部门
    url('^one_department$', views.one_department),  # 查单个部门详细信息
    url('^all_department$', views.all_department),  # 查询所有部门

    url('^add_staff$', views.add_staff),  # 添加员工
    url('^edit_staff$', views.edit_staff),  # 编辑员工
    url('^del_staff$', views.del_staff),  # 删除员工
    url('^all_staff$', views.all_staff),  # 查询员工
    url('^one_staff$', views.one_staff),  # 查询单条员工

    url('^add_item$', views.add_item),  # 添加条目
    url('^one_item$', views.one_item),  # 编辑前获取单条条目信息
    url('^edit_item$', views.edit_item),  # 编辑条目
    url('^del_item$', views.del_item),  # 删除条目
    url('^all_item$', views.all_item),  # 查询条目

    url('^upload_staff_file$', views.upload_staff_file),  # 上传自命名文档
    url('^staff_all_file$', views.staff_all_file),  # 查看某员工所有自命名文档
    url('^download_staff_file$', views.download_staff_file),  # 下载自命名文档

    url('export_staff', views.export_staff),  # 员工管理--导出员工模板
    url(r'staff_import', views.upload_staff),  # 员工管理--解析员工资料
    url(r'import_staff', views.import_staff),  # 解析员工调用单条添加，对应身份证已存在则不可改动

    url('^all_user$', views.all_user),  # 查询所有用户
    url('^all_item_user$', views.all_item_user),  # 条目用户关系管理，以用户id查询用户具有条目
    url('^all_item_owner$', views.all_item_owner),  # 以登陆用户查询所有条目
    url('^freash_item_user$', views.refresh_item_user),  # 用户具有条目清空后并且重新分配,'1|2|3'

    url('^add_teachitem$', views.add_teachitem),  # 对条目的细项进行添加
    url('^one_teachitem$', views.one_teachitem),  # 查询一个条目的细项
    url('^all_teachitem$', views.all_teachitem),  # 用中文'教学加班'、'德育补助'、'安全补助'查对应细项
    url('^edit_teachitem$', views.edit_teachitem),  # 对条目的细项进行编辑
    url('^del_teachitem$', views.del_teachitem),  # 对条目的细项进行删除

    url('^staff_courseprice$', views.staff_courseprice),  # 查某员工所有课程的课时费
    url('^one_unitprice$', views.one_unitprice),  # 编辑前查一条课时费记录
    url('^edit_unitprice$', views.edit_unitprice),  # 编辑某员工某课的课时单价
]
