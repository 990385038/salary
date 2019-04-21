# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class UserLog(models.Model):  # 用户日志
    User = models.ForeignKey(User)
    create_time = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(max_length=255)
