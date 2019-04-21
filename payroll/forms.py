# -*- coding:utf-8 -*-

from django import forms


class BulkAddattendance(forms.Form):
    department = forms.IntegerField()
    give_time = forms.CharField()
    refer_time = forms.CharField()


class EditAttendance(forms.Form):
    id = forms.IntegerField()
    rate = forms.FloatField()


class AllAttendance(forms.Form):
    give_time = forms.CharField()
    department = forms.IntegerField()


class EditPayroll(forms.Form):
    staff = forms.IntegerField()
    give_time = forms.CharField()
    item = forms.CharField()
    money = forms.FloatField()


class BulkAdd(forms.Form):
    department = forms.IntegerField()
    give_time = forms.CharField()
    refer_time = forms.CharField()


class TeachrollPreview(forms.Form):  # 预览哪个部门，哪个年月，所有细项的id
    department = forms.IntegerField()
    refer_time = forms.CharField()
    teachitem_id = forms.CharField()
    item_ch = forms.CharField()  # 三项的中文


class TeachrollView(forms.Form):
    department = forms.IntegerField()
    give_time = forms.CharField()


class AskPayrollVerify(forms.Form):
    give_time = forms.CharField()


class EditPayrollVerify(forms.Form):
    id = forms.CharField()


class ComparePayroll(forms.Form):
    verify_id = forms.IntegerField()
    give_time = forms.CharField()
    refer_time = forms.CharField()


class FreashPayroll(forms.Form):
    give_time = forms.CharField()


class ConfirmPayroll(forms.Form):
    id = forms.IntegerField()
    pay_date = forms.CharField()


class BulkAddteach(forms.Form):
    department = forms.IntegerField()
    three_part = forms.ChoiceField(choices=(('教学加班', 0), ('德育补助', 1), ('安全补助', 2)))
    give_time = forms.CharField()
    refer_time = forms.CharField()


# class AllPayrollteach(forms.Form):
#     department = forms.IntegerField()
#     three_part = forms.ChoiceField(choices=(('教学加班', 0), ('德育补助', 1), ('安全补助', 2)))
#     give_time = forms.CharField()


class PayrollPrevies(forms.Form):
    department_id = forms.IntegerField()
    refer_time = forms.CharField()
    items_id = forms.CharField()  # 'id1|id2|id3'


class PayrollView(forms.Form):
    department = forms.IntegerField()
    give_time = forms.CharField()


class TeachView(forms.Form):
    department = forms.IntegerField()
    give_time = forms.CharField()
    item_ch = forms.CharField()


# class BulkAddPayroll(forms.Form):  # 工资条目记录校验
#     json_data_str = forms.CharField(max_length=1024)
#
#     def clean(self):  # 重写clean，可以覆盖jaon_data_str，这里没覆盖
#         cleaned_data = self.cleaned_data
#         json_data = json.loads(cleaned_data["json_data_str"])
#         json_schema = {
#             "definitions": {},
#             "$schema": "http://json-schema.org/draft-07/schema#",
#             "$id": "http://example.com/root.json",
#             "type": "object",
#             "title": "The Root Schema",
#             "required": [
#                 "give_time",
#                 "each_staff"
#             ],
#             "properties": {
#                 "give_time": {
#                     "$id": "#/properties/give_time",
#                     "type": "string",
#                     "title": "The Give_time Schema",
#                     "default": "",
#                     "examples": [
#                         "2019-05"
#                     ],
#                     "pattern": "^(.*)$"
#                 },
#                 "each_staff": {
#                     "$id": "#/properties/each_staff",
#                     "type": "array",
#                     "title": "The Each_staff Schema",
#                     "items": {
#                         "$id": "#/properties/each_staff/items",
#                         "type": "object",
#                         "title": "The Items Schema",
#                         "required": [
#                             "each_item",
#                             "staff_id"
#                         ],
#                         "properties": {
#                             "each_item": {
#                                 "$id": "#/properties/each_staff/items/properties/each_item",
#                                 "type": "array",
#                                 "title": "The Each_item Schema",
#                                 "items": {
#                                     "$id": "#/properties/each_staff/items/properties/each_item/items",
#                                     "type": "object",
#                                     "title": "The Items Schema",
#                                     "required": [
#                                         "item_id",
#                                         "money"
#                                     ],
#                                     "properties": {
#                                         "item_id": {
#                                             "$id": "#/properties/each_staff/items/properties/each_item/items/properties/item_id",
#                                             "type": "integer",
#                                             "title": "The Item_id Schema",
#                                             "default": 0,
#                                             "examples": [
#                                                 1
#                                             ]
#                                         },
#                                         "money": {
#                                             "$id": "#/properties/each_staff/items/properties/each_item/items/properties/money",
#                                             "type": "integer",
#                                             "title": "The Money Schema",
#                                             "default": 0,
#                                             "examples": [
#                                                 66
#                                             ]
#                                         }
#                                     }
#                                 }
#                             },
#                             "staff_id": {
#                                 "$id": "#/properties/each_staff/items/properties/staff_id",
#                                 "type": "integer",
#                                 "title": "The Staff_id Schema",
#                                 "default": 0,
#                                 "examples": [
#                                     4
#                                 ]
#                             }
#                         }
#                     }
#                 }
#             }
#         }
#         try:
#             validate(json_data, json_schema)
#         except Exception as e:
#             raise forms.ValidationError(e)
#         return cleaned_data
#
#
# class BulkAddTeachroll(forms.Form):  # 教学条目细项记录校验
#     json_data_str = forms.CharField(max_length=1024)
#
#     def clean(self):  # 重写clean，可以覆盖jaon_data_str，这里没覆盖
#         cleaned_data = self.cleaned_data
#         json_data = json.loads(cleaned_data["json_data_str"])
#         json_schema = {
#             "type": "object",
#             "required": ["give_time", "item_id", "item_money", "each_staff"],
#             "properties": {
#                 "give_time": {"type": "string"},
#                 "item_id": {"type": "integer"},
#                 "item_money": {"type": "numver"},
#                 "each_staff": {
#                     "type": "array",
#                     "items": {
#                         "type": "object",
#                         "required": ["staff_id", "teachitems_hour", "teachitems_nohour"],
#                         "properties": {
#                             "staff_id": {"type": "integer"},
#                             "teachitems_hour": {
#                                 "type": "array",
#                                 "required": ["teachitem_id", "teach_time", "money"],
#                                 "properties": {
#                                     "teachitem_id": "integer",
#                                     "teach_time": "number",
#                                 }},
#                             "teachitems_nohour": {
#                                 "type": "array",
#                                 "required": ["teachitem_id", "money"],
#                                 "properties": {
#                                     "teachitem_id": "integer",
#                                     "money": "number",
#                                 }},
#                         }
#                     }
#                 },
#             }
#         }
#         try:
#             validate(json_data, json_schema)
#         except Exception as e:
#             raise forms.ValidationError(e)
#         return cleaned_data

class BulkAddPayroll(forms.Form):
    items_id = forms.CharField()
    refer_time = forms.CharField()
    department_id = forms.IntegerField()
    give_time = forms.CharField()


class BulkAddTeachroll(forms.Form):
    teachitem_id = forms.CharField()  # 条目的哪些细项
    refer_time = forms.CharField()
    department_id = forms.IntegerField()
    give_time = forms.CharField()
    item_ch = forms.CharField()


class OnePayroll(forms.Form):
    staff_id = forms.IntegerField()
    give_time = forms.CharField()


class EditOnePayroll(forms.Form):
    give_time = forms.CharField(max_length=1024)
    staff_id = forms.IntegerField()
    items = forms.CharField()


class OneTeachPayroll(forms.Form):
    staff_id = forms.IntegerField()
    give_time = forms.CharField()
    item_ch = forms.CharField()


class EditTeachPayroll(forms.Form):
    give_time = forms.CharField(max_length=1024)
    staff_id = forms.IntegerField()
    item_ch = forms.CharField()
    time_items = forms.CharField()
    notime_items = forms.CharField()

    # # 这样校验怕是有点小问题
    # def clean(self):  # 重写clean，可以覆盖jaon_data_str，这里没覆盖
    #     cleaned_data = self.cleaned_data
    #     json_data = json.loads(cleaned_data["json_data_str"])
    #     json_schema = {
    #         "definitions": {},
    #         "$schema": "http://json-schema.org/draft-07/schema#",
    #         "$id": "http://example.com/root.json",
    #         "type": "object",
    #         "title": "The Root Schema",
    #         "required": [
    #             "staff_id",
    #             "give_time",
    #             "items"
    #         ],
    #         "properties": {
    #             "staff_id": {
    #                 "$id": "#/properties/staff_id",
    #                 "type": "integer",
    #                 "title": "The Staff_id Schema",
    #                 "default": 0,
    #                 "examples": [
    #                     1
    #                 ]
    #             },
    #             "give_time": {
    #                 "$id": "#/properties/give_time",
    #                 "type": "string",
    #                 "title": "The Give_time Schema",
    #                 "default": "",
    #                 "examples": [
    #                     "2019-01"
    #                 ],
    #                 "pattern": "^(.*)$"
    #             },
    #             "items": {
    #                 "$id": "#/properties/items",
    #                 "type": "object",
    #                 "title": "The Items Schema",
    #                 "required": [
    #                     "1",
    #                     "2"
    #                 ],
    #                 "properties": {
    #                     "1": {
    #                         "$id": "#/properties/items/properties/1",
    #                         "type": "integer",
    #                         "title": "The 1 Schema",
    #                         "default": 0,
    #                         "examples": [
    #                             1000
    #                         ]
    #                     },
    #                     "2": {
    #                         "$id": "#/properties/items/properties/2",
    #                         "type": "integer",
    #                         "title": "The 2 Schema",
    #                         "default": 0,
    #                         "examples": [
    #                             2000
    #                         ]
    #                     }
    #                 }
    #             }
    #         }
    #     }
    #     try:
    #         validate(json_data, json_schema)
    #     except Exception as e:
    #         raise forms.ValidationError(e)
    #     return cleaned_data
