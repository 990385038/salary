# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-04-09 03:45
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, unique=True)),
                ('remark', models.CharField(max_length=32)),
                ('status', models.IntegerField(choices=[(0, '\u65e0\u6548'), (1, '\u6709\u6548')], default=1)),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32)),
                ('qiniu_name', models.CharField(max_length=32)),
                ('remark', models.CharField(default='', max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.IntegerField(choices=[(0, '\u5e94\u6263'), (1, '\u5e94\u53d1')])),
                ('sec_type', models.IntegerField(choices=[(0, '\u5e94\u6263'), (1, '\u6807\u51c6\u5de5\u8d44'), (2, '\u6559\u5b66\u5de5\u8d44'), (3, '\u5176\u4ed6\u5de5\u8d44')])),
                ('name', models.CharField(max_length=32, unique=True)),
                ('status', models.IntegerField(choices=[(0, '\u65e0\u6548'), (1, '\u6709\u6548')], default=1)),
                ('remark', models.CharField(default='', max_length=32)),
            ],
        ),
        migrations.CreateModel(
            name='ItemUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='basic.Item')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('id_card', models.CharField(max_length=32, unique=True)),
                ('name', models.CharField(max_length=32)),
                ('phone', models.CharField(max_length=32)),
                ('bank_card_num', models.CharField(max_length=32)),
                ('bank_name', models.CharField(max_length=32)),
                ('entry_date', models.DateTimeField()),
                ('tax_start', models.FloatField(default=5000)),
                ('status', models.IntegerField(choices=[(0, '\u79bb\u804c'), (1, '\u5728\u804c')], default=1)),
                ('remark', models.CharField(default='', max_length=32)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='basic.Department')),
            ],
        ),
        migrations.CreateModel(
            name='TeachItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.IntegerField(choices=[(0, '\u8ba1\u8bfe\u65f6'), (1, '\u8ba1\u603b\u8d39')])),
                ('name', models.CharField(max_length=32)),
                ('default_price', models.CharField(default='', max_length=32)),
                ('remark', models.CharField(default='', max_length=32)),
                ('status', models.IntegerField(choices=[(0, '\u65e0\u6548'), (1, '\u6709\u6548')], default=1)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='basic.Item')),
            ],
        ),
        migrations.CreateModel(
            name='UnitPrice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.FloatField(default=0)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='basic.TeachItem')),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='basic.Staff')),
            ],
        ),
        migrations.AddField(
            model_name='file',
            name='staff',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file', to='basic.Staff'),
        ),
        migrations.AlterUniqueTogether(
            name='unitprice',
            unique_together=set([('course', 'staff')]),
        ),
        migrations.AlterUniqueTogether(
            name='teachitem',
            unique_together=set([('item', 'type', 'name')]),
        ),
    ]
