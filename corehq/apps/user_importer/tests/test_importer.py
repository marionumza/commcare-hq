from copy import deepcopy

from django.test import TestCase

from mock import patch

from corehq.apps.accounting.tests.utils import DomainSubscriptionMixin
from corehq.apps.commtrack.tests.util import make_loc
from corehq.apps.domain.models import Domain
from corehq.apps.user_importer.importer import (
    create_or_update_users_and_groups,
)
from corehq.apps.user_importer.tasks import import_users_and_groups
from corehq.apps.users.dbaccessors.all_commcare_users import delete_all_users
from corehq.apps.users.models import CommCareUser, Permissions, UserRole


class TestUserBulkUpload(TestCase, DomainSubscriptionMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        delete_all_users()
        cls.domain_name = 'mydomain'
        cls.domain = Domain(name=cls.domain_name)
        cls.domain.save()

        permissions = Permissions(edit_apps=True, view_reports=True)
        cls.role = UserRole.get_or_create_with_permissions(cls.domain.name, permissions, 'edit-apps')

    @classmethod
    def tearDownClass(cls):
        cls.domain.delete()
        super().tearDownClass()

    def tearDown(self):
        delete_all_users()

    @property
    def user(self):
        return CommCareUser.get_by_username('{}@{}.commcarehq.org'.format(
            'hello',
            self.domain.name))

    def _get_spec(self, **kwargs):
        spec = {
            'username': 'hello',
            'name': 'Another One',
            'language': None,
            'is_active': 'True',
            'phone-number': '23424123',
            'password': 123,
            'email': None
        }
        spec.update(kwargs)
        return spec

    def test_upload_with_missing_user_id(self):
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(user_id='missing')],
            [],
        )

        self.assertIsNone(self.user)

    @patch('corehq.apps.user_importer.importer.domain_has_privilege', lambda x, y: True)
    def test_location_not_list(self):
        self.setup_locations()

        # location_code can also just be string instead of array for single location assignmentss
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(location_code=self.loc1.site_code)],
            [],
        )
        self.assertEqual(self.user.location_id, self.loc1._id)
        self.assertEqual(self.user.location_id, self.user.user_data.get('commcare_location_id'))
        # multiple locations
        self.assertListEqual([self.loc1._id], self.user.assigned_location_ids)

    @patch('corehq.apps.user_importer.importer.domain_has_privilege', lambda x, y: True)
    def test_location_unknown_site_code(self):
        self.setup_locations()

        # location_code should be an array of multiple excel columns
        # with self.assertRaises(UserUploadError):
        result = create_or_update_users_and_groups(
            self.domain.name,
            [self._get_spec(location_code='unknownsite')],
        )
        self.assertEqual(len(result["rows"]), 1)

    @patch('corehq.apps.user_importer.importer.domain_has_privilege', lambda x, y: True)
    def test_location_add(self):
        self.setup_locations()
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(location_code=[a.site_code for a in [self.loc1, self.loc2]])],
            [],
        )
        # first location should be primary location
        self.assertEqual(self.user.location_id, self.loc1._id)
        self.assertEqual(self.user.location_id, self.user.user_data.get('commcare_location_id'))
        # multiple locations
        self.assertListEqual([l._id for l in [self.loc1, self.loc2]], self.user.assigned_location_ids)
        # non-primary location
        self.assertTrue(self.loc2._id in self.user.user_data.get('commcare_location_ids'))

    @patch('corehq.apps.user_importer.importer.domain_has_privilege', lambda x, y: True)
    def test_location_remove(self):
        self.setup_locations()
        # first assign both locations
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(location_code=[a.site_code for a in [self.loc1, self.loc2]])],
            [],
        )

        # deassign all locations
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(location_code=[], user_id=self.user._id)],
            [],
        )

        # user should have no locations
        self.assertEqual(self.user.location_id, None)
        self.assertEqual(self.user.user_data.get('commcare_location_id'), None)
        self.assertListEqual(self.user.assigned_location_ids, [])

    @patch('corehq.apps.user_importer.importer.domain_has_privilege', lambda x, y: True)
    def test_primary_location_replace(self):
        self.setup_locations()
        # first assign to loc1
        create_or_update_users_and_groups(
            self.domain.name,
            [self._get_spec(location_code=[a.site_code for a in [self.loc1, self.loc2]])],
        )

        # user's primary location should be loc1
        self.assertEqual(self.user.location_id, self.loc1._id)
        self.assertEqual(self.user.user_data.get('commcare_location_id'), self.loc1._id)
        self.assertEqual(self.user.user_data.get('commcare_location_ids'), " ".join([self.loc1._id, self.loc2._id]))
        self.assertListEqual(self.user.assigned_location_ids, [self.loc1._id, self.loc2._id])

        # reassign to loc2
        create_or_update_users_and_groups(
            self.domain.name,
            [self._get_spec(location_code=[self.loc2.site_code], user_id=self.user._id)],
        )

        # user's location should now be loc2
        self.assertEqual(self.user.location_id, self.loc2._id)
        self.assertEqual(self.user.user_data.get('commcare_location_ids'), self.loc2._id)
        self.assertEqual(self.user.user_data.get('commcare_location_id'), self.loc2._id)
        self.assertListEqual(self.user.assigned_location_ids, [self.loc2._id])

    @patch('corehq.apps.user_importer.importer.domain_has_privilege', lambda x, y: True)
    def test_location_replace(self):
        self.setup_locations()

        # first assign to loc1
        create_or_update_users_and_groups(
            self.domain.name,
            [self._get_spec(location_code=[self.loc1.site_code])]
        )

        # reassign to loc2
        create_or_update_users_and_groups(
            self.domain.name,
            [self._get_spec(location_code=[self.loc2.site_code], user_id=self.user._id)]
        )

        # user's location should now be loc2
        self.assertEqual(self.user.location_id, self.loc2._id)
        self.assertEqual(self.user.user_data.get('commcare_location_id'), self.loc2._id)
        self.assertListEqual(self.user.assigned_location_ids, [self.loc2._id])

    def setup_locations(self):
        self.loc1 = make_loc('loc1', type='state', domain=self.domain_name)
        self.loc2 = make_loc('loc2', type='state', domain=self.domain_name)

    def test_numeric_user_name(self):
        """
        Test that bulk upload doesn't choke if the user's name is a number
        """
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(name=1234)],
            [],
        )
        self.assertEqual(self.user.full_name, "1234")

    def test_empty_user_name(self):
        """
        This test confirms that a name of None doesn't set the users name to
        "None" or anything like that.
        """
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(name=None)],
            [],
        )
        self.assertEqual(self.user.full_name, "")

    def test_upper_case_email(self):
        """
        Ensure that bulk upload throws a proper error when the email has caps in it
        """
        email = 'IlOvECaPs@gmaiL.Com'
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(email=email)],
            [],
        )
        self.assertEqual(self.user.email, email.lower())

    def test_set_role(self):
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(role=self.role.name)],
            [],
        )
        self.assertEqual(self.user.get_role(self.domain_name).name, self.role.name)

    def test_blank_is_active(self):
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(is_active='')],
            [],
        )
        self.assertTrue(self.user.is_active)

    def test_update_user_no_username(self):
        import_users_and_groups(
            self.domain.name,
            [self._get_spec()],
            [],
        )
        self.assertIsNotNone(self.user)

        import_users_and_groups(
            self.domain.name,
            [self._get_spec(user_id=self.user._id, username='')],
            [],
        )

    def test_update_user_numeric_username(self):
        import_users_and_groups(
            self.domain.name,
            [self._get_spec(username=123)],
            [],
        )
        self.assertIsNotNone(
            CommCareUser.get_by_username('{}@{}.commcarehq.org'.format('123', self.domain.name))
        )


class TestUserBulkUploadStrongPassword(TestCase, DomainSubscriptionMixin):
    def setUp(self):
        super(TestUserBulkUploadStrongPassword, self).setUp()
        delete_all_users()
        self.domain_name = 'mydomain'
        self.domain = Domain(name=self.domain_name)
        self.domain.strong_mobile_passwords = True
        self.domain.save()
        self.user_specs = [{
            'username': 'tswift',
            'user_id': '1989',
            'name': 'Taylor Swift',
            'language': None,
            'is_active': 'True',
            'phone-number': '8675309',
            'password': 'TaylorSwift89!',
            'email': None
        }]

    def tearDown(self):
        self.domain.delete()
        super(TestUserBulkUploadStrongPassword, self).tearDown()

    def test_duplicate_password(self):
        user_spec = [{
            'username': 'thiddleston',
            'user_id': '1990',
            'name': 'Tom Hiddleston',
            'language': None,
            'is_active': 'True',
            'phone-number': '8675309',
            'password': 'TaylorSwift89!',
            'email': None
        }]

        rows = import_users_and_groups(
            self.domain.name,
            list(user_spec + self.user_specs),
            [],
        )['messages']['rows']
        self.assertEqual(rows[0]['flag'], "'password' values must be unique")

    def test_weak_password(self):
        updated_user_spec = deepcopy(self.user_specs[0])
        updated_user_spec["password"] = '123'

        rows = import_users_and_groups(
            self.domain.name,
            list([updated_user_spec]),
            [],
        )['messages']['rows']
        self.assertEqual(rows[0]['flag'], 'Password is not strong enough. Try making your password more complex.')
