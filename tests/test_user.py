import json

from tests.base_test import BaseTest
from app.email_service import TEST_MESSAGES
from app.models import User, EmailLog


class TestUser(BaseTest):
    def test_create_user_with_password(self):
        self.create_user_with_password()

    def test_get_current_participant(self):
        """ Test for the current participant status """
        # Create the user
        headers = {
            'eppn': self.test_eppn,
            'givenName': 'Daniel',
            'mail': 'dhf8r@virginia.edu'
        }
        rv = self.app.get(
            "/api/login",
            headers=headers,
            follow_redirects=True,
            content_type="application/json")
        # Don't check success, login does a redirect to the
        # front end that might not be running.
        # self.assert_success(rv)

        user = User.query.filter_by(eppn=self.test_eppn).first()

        # Now get the user back.
        response = self.app.get(
            '/api/session',
            headers=dict(
                Authorization='Bearer ' + user.encode_auth_token().decode()))
        self.assertSuccess(response)
        return json.loads(response.data.decode())

    def test_user_owner_should_always_be_able_to_view_their_own_resources(
            self):
        institution = self.construct_institution(
            name="University of Galactic Domination",
            domain="senate.galaxy.gov")

        u = self.construct_user(
            eppn="jjb@senate.galaxy.gov",
            display_name="Jar Jar Binks",
            email="jjb@senate.galaxy.gov",
            institution=institution)

        resources = self.construct_various_resources(institution=institution, owner=u.email)
        self.assertEqual(16, len(resources))

        rv = self.app.get(
            '/api/resource',
            query_string={'limit': '16'},
            follow_redirects=True,
            content_type="application/json",
            headers=self.logged_in_headers(user=u))
        self.assertSuccess(rv)
        result = json.loads(rv.get_data(as_text=True))

        # General user owns only 8 of the 16 resources, but can also
        # see the 3 approved resources from other institutions
        self.assertEqual(11, len(result))

        # Search endpoint should return the same number of results
        search_results = self.search({}, user=u)
        self.assertEqual(len(result), search_results['total'])

    def test_user_email_is_case_insensitive(self):
        password = "s00p3rS3cur3"
        email = email="Darth.maul@sith.net"
        user = self.logout_user(
            display_name="Darth Maul",
            eppn="DARTH.MAUL@sith.net",
            email=email,
            role="User",
            password=password
        )

        emails = [
            "darth.maul@sith.net",
            "DARTH.MAUL@SITH.NET",
            "Darth.Maul@Sith.Net",
            "dArTh.mAuL@sItH.nEt"
        ]

        for email_variant in emails:
            data = {"email": email_variant, "password": password}

            # Should be able to log in successfully
            rv = self.app.post(
                '/api/login_password',
                data=json.dumps(data),
                content_type="application/json")
            self.assertSuccess(rv)
            response = json.loads(rv.get_data(as_text=True))
            self.assertIsNotNone(response["token"])

            # Log out
            rv = self.app.delete('/api/session',
                content_type="application/json",
                headers=self.logged_in_headers(user))
            self.assertSuccess(rv)

            # Make sure user can retrieve password
            message_count = len(TEST_MESSAGES)
            rv = self.app.post(
                '/api/forgot_password',
                data=json.dumps({"email": email_variant}),
                content_type="application/json")
            self.assertSuccess(rv)
            self.assertGreater(len(TEST_MESSAGES), message_count)
            self.assertEqual("iTHRIV: Password Reset Email", self.decode(TEST_MESSAGES[-1]['subject']))

            logs = EmailLog.query.all()
            self.assertIsNotNone(logs[-1].tracking_code)
