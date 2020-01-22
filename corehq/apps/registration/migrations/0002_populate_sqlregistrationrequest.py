# -*- coding: utf-8 -*-

import sys
import traceback

from django.core.management import call_command
from django.db import migrations

from corehq.apps.registration.models import SQLRegistrationRequest
from corehq.dbaccessors.couchapps.all_docs import get_doc_ids_by_class
from corehq.util.django_migrations import skip_on_fresh_install


AUTO_MIGRATE_ITEMS_LIMIT = 1000
AUTO_MIGRATE_FAILED_MESSAGE = """
    A migration must be performed before this environment can be upgraded to the latest version of CommCareHQ.
    This migration is run using the management command populate_sql_registration_request
"""


def count_items_to_be_migrated():
    try:
        from corehq.apps.registration.models import RegistrationRequest
    except ImportError:
        return 0
    couch_count = len(get_doc_ids_by_class(RegistrationRequest))
    sql_count = SQLRegistrationRequest.objects.count()
    return couch_count - sql_count


@skip_on_fresh_install
def _verify_sql_registration_request(apps, schema_editor):
    to_migrate = count_items_to_be_migrated()
    migrated = to_migrate == 0
    if migrated:
        return

    if to_migrate < AUTO_MIGRATE_ITEMS_LIMIT:
        try:
            call_command('populate_sql_registration_request')
            migrated = count_items_to_be_migrated() == 0
            if not migrated:
                print("Automatic migration failed")
        except Exception:
            traceback.print_exc()
    else:
        print("Found {} items that need to be migrated.".format(to_migrate))
        print("Too many to migrate automatically.")

    if not migrated:
        print("")
        print(AUTO_MIGRATE_FAILED_MESSAGE)
        sys.exit(1)


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(_verify_sql_registration_request,
                             reverse_code=migrations.RunPython.noop,
                             elidable=True),
    ]
