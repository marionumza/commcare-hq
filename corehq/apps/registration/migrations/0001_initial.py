# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-01-22 02:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SQLRegistrationRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tos_confirmed', models.BooleanField(default=False)),
                ('request_time', models.DateTimeField()),
                ('request_ip', models.CharField(max_length=31)),
                ('activation_guid', models.CharField(max_length=126)),
                ('confirm_time', models.DateTimeField(null=True)),
                ('confirm_ip', models.CharField(max_length=31, null=True)),
                ('domain', models.CharField(max_length=255, null=True)),
                ('new_user_username', models.CharField(max_length=255, null=True)),
                ('requesting_user_username', models.CharField(max_length=255, null=True)),
            ],
            options={
                'db_table': 'registrationrequest',
            },
        ),
    ]
