# -*- coding:utf-8 -*-
from django import forms


class AddDepartment(forms.Form):
    name = forms.CharField(max_length=255)
    remark = forms.CharField(max_length=255)


class EditDepartment(forms.Form):
    id = forms.IntegerField()
    name = forms.CharField(max_length=255)
    remark = forms.CharField(max_length=255)


class DelDepartment(forms.Form):
    id = forms.IntegerField()


class OneDepartment(forms.Form):
    id = forms.IntegerField()


class AddStaff(forms.Form):
    id_card = forms.CharField(max_length=255)
    name = forms.CharField(max_length=255)
    phone = forms.CharField(max_length=255)
    department = forms.IntegerField()
    bank_card_num = forms.CharField(max_length=255)
    bank_name = forms.CharField(max_length=255)
    entry_date = forms.CharField(max_length=255)
    tax_start = forms.FloatField()
    remark = forms.CharField(max_length=255)


class EditStaff(forms.Form):
    id = forms.IntegerField()
    id_card = forms.CharField(max_length=255)
    name = forms.CharField(max_length=255)
    phone = forms.CharField(max_length=255)
    department = forms.IntegerField()
    bank_card_num = forms.CharField(max_length=255)
    bank_name = forms.CharField(max_length=255)
    entry_date = forms.CharField(max_length=255)
    tax_start = forms.FloatField()
    remark = forms.CharField(max_length=255)


class DelStaff(forms.Form):
    id = forms.IntegerField()


class OneUnitprice(forms.Form):
    id = forms.IntegerField()


class EditUnitprice(forms.Form):
    id = forms.IntegerField()
    price = forms.FloatField()


class StaffCourseprice(forms.Form):
    id = forms.IntegerField()


class UploadStafffile(forms.Form):  # 员工上传文件的名字，员工id，员工的备注
    name = forms.CharField(max_length=255)
    staff = forms.IntegerField()
    remark = forms.CharField(max_length=255)


class OneStaff(forms.Form):
    id = forms.IntegerField()


class StaffAllfile(forms.Form):
    id = forms.IntegerField()


class DownloadStafffile(forms.Form):
    qiniu_name = forms.CharField(max_length=255)


class ImportStaff(forms.Form):
    name = forms.CharField(max_length=255)
    phone = forms.CharField(max_length=255)
    id_card = forms.CharField(max_length=255)
    bank_card_num = forms.CharField(max_length=255)
    bank_name = forms.CharField(max_length=255)
    tax_start = forms.CharField(max_length=255)
    department = forms.CharField(max_length=255)
    entry_date = forms.CharField(max_length=255)
    remark = forms.CharField(max_length=255)


class AddItem(forms.Form):
    type = forms.ChoiceField(choices=(('应扣', 0), ('应发', 1)))
    sec_type = forms.ChoiceField(choices=(('应扣', 0), ('标准工资', 1), ('教学工资', 2), ('其他工资', 3)))
    name = forms.CharField(max_length=255)
    remark = forms.CharField(max_length=255)


class OneItem(forms.Form):
    id = forms.IntegerField()


class EditItem(forms.Form):
    id = forms.IntegerField()
    type = forms.ChoiceField(choices=(('应扣', 0), ('应发', 1)))
    sec_type = forms.ChoiceField(choices=(('应扣', 0), ('标准工资', 1), ('教学工资', 2), ('其他工资', 3), ('三项', 4)))
    name = forms.CharField(max_length=255)
    remark = forms.CharField(max_length=255)


class DelItem(forms.Form):
    id = forms.IntegerField()


class AllItemUser(forms.Form):
    id = forms.IntegerField()


class RefreshItemUser(forms.Form):
    user_id = forms.IntegerField()
    item_id_str = forms.CharField()  # 条目字符串'1|2|3|4|5'


class AddTeachitem(forms.Form):
    id = forms.IntegerField()
    type = forms.ChoiceField(choices=((0, '计课时'), (1, '计总费')))
    # type = forms.IntegerField()
    name = forms.CharField(max_length=255)
    default_price = forms.FloatField()
    # default_price = forms.IntegerField()
    remark = forms.CharField(max_length=255)


class OneTeachitem(forms.Form):
    id = forms.IntegerField()


class AllTeachitem(forms.Form):
    item_ch = forms.CharField()


class EditTeachitem(forms.Form):
    id = forms.IntegerField()
    type = forms.IntegerField()
    name = forms.CharField(max_length=255)
    remark = forms.CharField(max_length=255)
    default_price = forms.FloatField()


class DelTeachitem(forms.Form):
    id = forms.IntegerField()
