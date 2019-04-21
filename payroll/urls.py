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

from payroll import views

# 工资记录审核状态由它外键到的审核记录代表，每个用户每个年月只能申请一次审批。。
# 工资记录—工资审核记录—工资发放记录
urlpatterns = [
    url('^bulk_add_attendance$', views.bulk_add_attendance),  # 批量生成某年月某部门出勤率,参考某年月
    url('^edit_attendance$', views.edit_attendance),  # 编辑考勤记录
    url('^all_attendance$', views.all_attendance),  # 查某部门某年月考勤记录

    # 工资记录的生成：对条目=预览-生成-查看，预览和查看都是查看，但是预览根据当前员工和指定条目参照指定年月进行生成
    # 预览，而查看是基于真实存在的工资记录查看，所以分两个接口，对某个条目的细项=预览-生成-查看，同理
    # 从结果上说，参照一个月，预览某月的展示效果和查看某月的展示效果一样
    url('^payroll_preview$', views.payroll_preview),
    url('^payroll_view$', views.payroll_view),
    url('^bulk_add_payroll$', views.bulk_add_payroll),  # 批量生成工资记录（对应的申请状态为暂存）

    # 预览（教学加班，德育补助，安全补助）细项工资记录
    url('^teachroll_priview$', views.teachroll_priview),
    url('^teachroll_view$', views.teachroll_view),
    # 批量生成教学（教学，加班，德育）细项目记录
    url('^bulk_add_teachroll$', views.bulk_add_teachroll),

    # 申请审批工资记录，某用户对某年月提交审核
    url('^ask_payroll_verify$', views.ask_payroll_verify),
    # 取消申请审核工资记录
    url('^cancel_payroll_verify$', views.cancel_payroll_verify),
    # 查询所有未审核工资记录,有效
    url('^effect_payroll_verify$', views.effect_payroll_verify),
    # 查所有审核记录
    url('^all_payroll_verify$', views.all_payroll_verify),

    # 选定一条审核记录，根据发薪年月和参考年月查出所有工资记录进行对比，情况：两个年月条目不一致
    # 先查出该审核记录的所有条目，再根据条目去找两个年月的工资记录
    url('^compare_payroll$', views.compare_payroll),

    # 将审核记录审核通过/失败
    url('^agree_payroll_verify$', views.agree_payroll_verify),
    url('^disagree_payroll_verify$', views.disagree_payroll_verify),

    # 添改工资发放记录
    url('^freash_payroll_records$', views.freash_payroll_records),
    # 查看工资发放记录
    url('^all_payroll_records$', views.all_payroll_records),
    # 确认工资发放记录（高级别)
    url('^confirm_payroll_records$', views.confirm_payroll_records),

    # 用员工id和发薪年月获取该员工的条目工资记录
    url('^one_payroll$', views.one_payroll),
    # 编辑单条员工工资记录
    url('^edit_one_payroll$', views.edit_one_payroll),

    # 用员工id和条目id和发薪年月获取该员工的细项记录
    url('^one_teach_payroll$', views.one_teach_payroll),
    # 编辑单条员工细项记录
    url('^edit_one_teach_payroll$', views.edit_one_teach_payroll),

    # 工资汇总
    # url('^payroll_total$', views.payroll_total),

    # 导出银行表
    # url('^export_bank$', views.export_bank),
]
