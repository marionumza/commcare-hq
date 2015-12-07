# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from corehq.form_processor.models import XFormInstanceSQL, XFormOperationSQL, CaseTransaction
from corehq.util.migration import RawSQLMigration


migrator = RawSQLMigration(('corehq', 'sql_accessors', 'sql_functions'), {
    'FORM_STATE_ARCHIVED': XFormInstanceSQL.ARCHIVED,
    'FORM_STATE_NORMAL': XFormInstanceSQL.NORMAL,
    'FORM_OPERATION_ARCHIVE': XFormOperationSQL.ARCHIVE,
    'FORM_OPERATION_UNARCHIVE': XFormOperationSQL.UNARCHIVE,
    'TRANSACTION_TYPE_LEDGER': CaseTransaction.TYPE_LEDGER,
    'TRANSACTION_TYPE_FORM': CaseTransaction.TYPE_FORM,
})


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrator.get_migration('archive_unarchive_form.sql'),
        migrator.get_migration('case_modified_since.sql'),
        migrator.get_migration('check_form_exists.sql'),
        migrator.get_migration('deprecate_form.sql'),
        migrator.get_migration('get_case_attachment_by_name.sql'),
        migrator.get_migration('get_case_attachments.sql'),
        migrator.get_migration('get_case_by_id.sql'),
        migrator.get_migration('get_case_by_location_id.sql'),
        migrator.get_migration('get_case_form_ids.sql'),
        migrator.get_migration('get_case_ids_in_domain.sql'),
        migrator.get_migration('get_case_indices.sql'),
        migrator.get_migration('get_case_indices_reverse.sql'),
        migrator.get_migration('get_case_transactions.sql'),
        migrator.get_migration('get_case_transactions_for_rebuild.sql'),
        migrator.get_migration('get_cases_by_id.sql'),
        migrator.get_migration('get_form_attachment_by_name.sql'),
        migrator.get_migration('get_form_attachments.sql'),
        migrator.get_migration('get_form_by_id.sql'),
        migrator.get_migration('get_form_ids_in_domain.sql'),
        migrator.get_migration('get_form_operations.sql'),
        migrator.get_migration('get_forms_by_id.sql'),
        migrator.get_migration('get_forms_by_state.sql'),
        migrator.get_migration('get_multiple_cases_indices.sql'),
        migrator.get_migration('get_multiple_forms_attachments.sql'),
        migrator.get_migration('get_reverse_indexed_cases.sql'),
        migrator.get_migration('hard_delete_cases.sql'),
        migrator.get_migration('hard_delete_forms.sql'),
        migrator.get_migration('revoke_restore_case_transactions_for_form.sql'),
        migrator.get_migration('save_case_and_related_models.sql'),
        migrator.get_migration('save_new_form_with_attachments.sql'),
        migrator.get_migration('update_form_problem_and_state.sql'),
    ]
