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
        self.assertEqual(
            1, len(
                User.query.filter(User.email == 'ehb11@virginia.edu').all()))

    def test_login_user(self, display_name="Kit Harington", eppn="jonsnow@got.com",
                                       email="jonsnow@got.com", role="User", password="y0ukn0wn0th!ng"):
        user = self.test_create_user_with_password(display_name=display_name, eppn=eppn,
                                       email=email, role=role, password=password)
        data = {"email": email, "password": password}

        # Login shouldn't work with email not yet verified
        rv = self.app.post(
            '/api/login_password',
            data=json.dumps(data),
            content_type="application/json")
        self.assertEqual(400, rv.status_code)

        user.email_verified = True
        rv = self.app.post(
            '/api/login_password',
            data=json.dumps(data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertIsNotNone(response["token"])

        return user

    def test_logout_user(self, display_name="Emilia Clarke", eppn="daeneryst@got.com",
                                       email="daeneryst@got.com", role="User", password="5t0rmb0r~"):
        user = self.test_login_user(display_name=display_name, eppn=eppn,
                                       email=email, role=role, password=password)
        rv = self.app.delete('/api/session',
            content_type="application/json",
            headers=self.logged_in_headers(user))
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertIsNone(response)

        return user
