# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-07-12 17:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0009_applicationdim_applicationstagingtable'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='completed_on',
            field=models.DateTimeField(null=True),
        ),
    ]
