from __future__ import absolute_import
from __future__ import unicode_literals

import json

from django.test import TestCase
from mock import patch

from corehq.apps.api.odata.tests.utils import OdataTestMixin
from corehq.util.test_utils import flag_enabled


class TestServiceDocument(OdataTestMixin, TestCase):

    view_urlname = 'odata_service'

    @flag_enabled('ODATA')
    def test_no_case_types(self):
        correct_credentials = self._get_correct_credentials()
        with patch('corehq.apps.api.odata.views.get_case_types_for_domain_es', return_value=set()):
            response = self._execute_query(correct_credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {"@odata.context": "http://localhost:8000/a/test_domain/api/v0.5/odata/Cases/$metadata", "value": []}
        )

    @flag_enabled('ODATA')
    def test_with_case_types(self):
        correct_credentials = self._get_correct_credentials()
        with patch(
            'corehq.apps.api.odata.views.get_case_types_for_domain_es',
            return_value=['case_type_1', 'case_type_2'],  # return ordered iterable for deterministic test
        ):
            response = self._execute_query(correct_credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {
                "@odata.context": "http://localhost:8000/a/test_domain/api/v0.5/odata/Cases/$metadata",
                "value": [
                    {'kind': 'EntitySet', 'name': 'case_type_1', 'url': 'case_type_1'},
                    {'kind': 'EntitySet', 'name': 'case_type_2', 'url': 'case_type_2'},
                ],
            }
        )
