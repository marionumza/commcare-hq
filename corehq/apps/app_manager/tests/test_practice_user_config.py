from django.test import TestCase

from corehq.apps.app_manager.exceptions import PracticeUserException
from corehq.apps.app_manager.models import Application, BuildProfile
from corehq.apps.domain.shortcuts import create_domain
from corehq.apps.ota.utils import turn_on_demo_mode, turn_off_demo_mode
from corehq.apps.users.models import CommCareUser

from .app_factory import AppFactory
from .util import TestXmlMixin


class TestPracticeUserRestore(TestCase, TestXmlMixin):
    """Tests for Practice Mobile Worker feature"""
    file_path = ('data',)

    @classmethod
    def setUpClass(cls):
        super(TestPracticeUserRestore, cls).setUpClass()
        from corehq.apps.users.dbaccessors.all_commcare_users import delete_all_users
        delete_all_users()
        cls.domain = "practice-user-domain"

        cls.factory = AppFactory(build_version='2.28.0', domain=cls.domain)
        module, form = cls.factory.new_basic_module('register', 'case')
        form.source = cls.get_xml('very_simple_form')

        cls.project = create_domain(cls.domain)
        cls.user = CommCareUser.create(cls.domain, 'test@main-domain.commcarehq.org', 'secret')

    def assert_(self, app, expected_paths):
        # test user-restore files created
        # test resource blocks created
        app.create_build_files

    def tearDown(self):
        turn_off_demo_mode(self.user)

    @staticmethod
    def _get_restore_resource(version, build_profile_id=None):
        extra = "?profile={id}".format(id=build_profile_id) if build_profile_id else ""
        return """
        <partial>
        <user-restore>
           <resource id="practice-user-restore" version="{version}" descriptor="practice user restore">
             <location authority="local">./practice_user_restore.xml</location>
             <location authority="remote">./practice_user_restore.xml{extra}</location>
           </resource>
        </user-restore>
        </partial>
        """.format(version=version, extra=extra)

    def test_app_specific(self):
        turn_on_demo_mode(self.user, self.domain)
        app = self.factory.app
        app.practice_mobile_worker_id = self.user._id

        # check suit contains user-restore resource
        self.assertXmlPartialEqual(
            self._get_restore_resource(self.user.demo_restore_id),
            app.create_suite(),
            "./user-restore"
        )
        # check 'files/practice_user_restore.xml' is included in the build files
        app.create_build_files(save=True)
        app.save()
        self.assertTrue(app.lazy_fetch_attachment('files/practice_user_restore.xml'))

    def test_profile_specific(self):
        turn_on_demo_mode(self.user, self.domain)
        app = self.factory.app
        build_profile_id = "some_uuid"
        app.build_profiles[build_profile_id] = BuildProfile(
            langs=['en'], name='en-profile', practice_mobile_worker_id=self.user._id
        )

        self.assertXmlPartialEqual(
            self._get_restore_resource(self.user.demo_restore_id, build_profile_id),
            app.create_suite(build_profile_id=build_profile_id),
            "./user-restore"
        )
        app.create_build_files(save=True, build_profile_id=build_profile_id)
        app.save()
        self.assertTrue(app.lazy_fetch_attachment('files/practice_user_restore.xml'))

    def test_bad_config(self):
        # if the user set as practice user for an app is not practice user, build should raise error

        # refetch so that memoized app.get_practice_user gets busted
        app = Application.get(self.factory.app._id)
        app.practice_mobile_worker_id = self.user._id

        self.assertIn(
            'practice user config error',
            [error['type'] for error in app.validate_app()]
        )
        with self.assertRaises(PracticeUserException):
            app.create_all_files()

    def test_update_user_restore(self):
        # updating user restore should result in version change in restore resource
        #   so that CommCare mobile will refetch the resource
        turn_on_demo_mode(self.user, self.domain)
        app = self.factory.app
        app.practice_mobile_worker_id = self.user._id

        # refetch so that memoized app.get_practice_user gets busted
        app = Application.get(app._id)
        self.assertXmlPartialEqual(
            self._get_restore_resource(self.user.demo_restore_id),
            app.create_suite(),
            "./user-restore"
        )

        version_beofre = self.user.demo_restore_id
        turn_off_demo_mode(self.user)
        turn_on_demo_mode(self.user, self.domain)
        version_after = self.user.demo_restore_id
        self.assertNotEqual(version_beofre, version_after)

        # refetch so that memoized app.get_practice_user gets busted`
        app = Application.get(app._id)
        self.assertXmlPartialEqual(
            self._get_restore_resource(self.user.demo_restore_id),
            app.create_suite(),
            "./user-restore"
        )

    # def test_commcare_version(self):
