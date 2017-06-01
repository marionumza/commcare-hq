# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-01 18:37
from __future__ import unicode_literals

from django.db import migrations

from corehq.sql_db.operations import HqRunSQL
from corehq.util.django_migrations import add_if_not_exists


class Migration(migrations.Migration):

    dependencies = [
        ('phonelog', '0007_devicelog_indexes'),
    ]

    operations = [
        HqRunSQL(
            add_if_not_exists(
                """
                CREATE INDEX phonelog_devicereportentry_domain_device_id_pattern_ops
                ON phonelog_devicereportentry (domain varchar_pattern_ops, device_id varchar_pattern_ops);
                """
            ),
            reverse_sql=
            """
            DROP INDEX IF EXISTS phonelog_devicereportentry_domain_device_id_pattern_ops;
            """,
        )
    ]
