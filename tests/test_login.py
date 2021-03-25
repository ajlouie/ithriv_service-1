import json

from tests.base_test import BaseTest
from app import db
from app.models import ThrivInstitution, User


class TestLogin(BaseTest):
    def test_sso_login_sets_institution_to_uva_correctly(self):
        inst_obj = ThrivInstitution(name="UVA", domain='virginia.edu')
        db.session.add(inst_obj)
        user = User(
            eppn="dhf8r@virginia.edu",
            display_name='Dan Funk',
            email='dhf8r@virginia.edu')
        self.logged_in_headers(user)
        dbu = User.query.filter_by(eppn='dhf8r@virginia.edu').first()
        self.assertIsNotNone(dbu)
        self.assertIsNotNone(dbu.institution)
        self.assertEqual('UVA', dbu.institution.name)

    def test_sso_login_with_existing_email_address_doesnt_bomb_out(self):
        # There is an existing user in the database, but it has no eppn.
        user = User(
            display_name='Engelbert Humperdinck', email='ehb11@virginia.edu')
        db.session.add(user)
        db.session.commit()
        # Log in via sso as a user with an eppn that matches an
        # existing users email address.
        user2 = User(
            eppn="ehb11@virginia.edu",
            display_name='Engelbert Humperdinck',
            email='ehb11@virginia.edu')

        headers = {
            'eppn': user.eppn,
            'givenName': user.display_name,
            'mail': user.email
        }

        rv = self.app.get(
            "/api/login",
            headers=headers,
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)

        db_user = User.query.filter_by(eppn=user.eppn).first()
        auth_token = dict(
            Authorization='Bearer ' + db_user.encode_auth_token().decode())

        # No errors occur when this user logs in, and we only have one
        # account with that email address.
        self.assertEqual(1, len(User.query.filter(User.email == 'ehb11@virginia.edu').all()))

    def test_login_user(self):
        self.login_user()

    def test_logout_user(self):
        self.logout_user()
