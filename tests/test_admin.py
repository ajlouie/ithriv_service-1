import json

from tests.base_test import BaseTest
from app import db
from app.models import User
from app.resources.schema import UserSchema


class TestAdmin(BaseTest):

    def test_admin_get_users(self):
        rv = self.app.get('/api/user')
        self.assertEqual(rv.status, "401 UNAUTHORIZED")

        rv = self.app.get(
            '/api/user',
            content_type="application/json",
            headers=self.logged_in_headers())
        self.assertSuccess(rv)

    def test_admin_update_user(self):
        user = self.test_create_user_with_password()
        user.name = "The Artist Formerly Known As Prince"
        rv = self.app.put(
            '/api/user/%i' % user.id,
            data=json.dumps(UserSchema().dump(user).data),
            content_type="application/json")
        self.assertEqual(rv.status, "401 UNAUTHORIZED")

        rv = self.app.put(
            '/api/user/%i' % user.id,
            data=json.dumps(UserSchema().dump(user).data),
            content_type="application/json",
            headers=self.logged_in_headers())
        self.assertSuccess(rv)

    def test_admin_delete_user(self):
        admin_user = self.construct_admin_user()
        user = self.construct_user()
        rv = self.app.delete(
            '/api/user/%i' % user.id, content_type="application/json")
        self.assertEqual(rv.status, "401 UNAUTHORIZED")

        rv = self.app.delete(
            '/api/user/%i' % user.id,
            content_type="application/json",
            headers=self.logged_in_headers(user=admin_user))
        self.assertSuccess(rv)


    def test_find_users_respects_pageSize(self):
        self.construct_various_users()

        query = {
            'filter': '',
            'sortOrder': 'asc',
            'pageNumber': '0',
            'pageSize': '1'
        }
        response = self.searchUsers(query)
        self.assertEqual(1, len(response['items']))

        query = {
            'filter': '',
            'sortOrder': 'asc',
            'pageNumber': '0',
            'pageSize': '2'
        }
        response = self.searchUsers(query)
        self.assertEqual(2, len(response['items']))

    def test_find_users_respects_pageNumber(self):
        self.construct_various_users()
        self.assertEqual(3, len(db.session.query(User).all()))

        query = {
            'filter': '',
            'sort': 'display_name',
            'sortOrder': 'asc',
            'pageNumber': '0',
            'pageSize': '2'
        }
        response = self.searchUsers(query)
        self.assertEqual(2, len(response['items']))
        self.assertEqual(3, response['total'])
        self.assertEqual('Big Bird', response['items'][0]['display_name'])

        query['pageNumber'] = 1
        response = self.searchUsers(query)
        self.assertEqual(1, len(response['items']))
        self.assertEqual('Oscar the Grouch',
                         response['items'][0]['display_name'])

        query['pageNumber'] = 2
        response = self.searchUsers(query)
        self.assertEqual(0, len(response['items']))

    def test_find_users_respects_filter(self):
        self.construct_various_users()
        query = {
            'filter': 'big',
            'sortOrder': 'asc',
            'pageNumber': '0',
            'pageSize': '20'
        }
        response = self.searchUsers(query)
        self.assertEqual(1, len(response['items']))

        query = {
            'filter': 'Grouch',
            'sortOrder': 'asc',
            'pageNumber': '0',
            'pageSize': '20'
        }
        response = self.searchUsers(query)
        self.assertEqual(1, len(response['items']))

        query = {
            'filter': '123',
            'sortOrder': 'asc',
            'pageNumber': '0',
            'pageSize': '20'
        }
        response = self.searchUsers(query)
        self.assertEqual(1, len(response['items']))

        query = {
            'filter': 'Ididnputthisinthedata',
            'sortOrder': 'asc',
            'pageNumber': '0',
            'pageSize': '20'
        }
        response = self.searchUsers(query)
        self.assertEqual(0, len(response['items']))

    def test_find_users_orders_results(self):
        db.session.query(User).delete()
        users_before = db.session.query(User).all()
        self.assertEqual(len(users_before), 0)

        users = self.construct_various_users()
        users_next = db.session.query(User).all()
        self.assertEqual(len(users_next), 3)

        admin_user = users[1]
        self.assertEqual(admin_user.role, "Admin")

        normal_user = users[0]
        self.assertEqual(normal_user.role, "User")

        q1 = {
            'filter': '',
            'sort': 'display_name',
            'sortOrder': 'asc',
            'pageNumber': '0',
            'pageSize': '20'
        }
        response = self.searchUsers(query=q1, user=admin_user)
        # users_after1 = db.session.query(User).all()
        # self.assertEqual(len(users_after1), 3)

        self.assertEqual(admin_user.display_name,
                         response['items'][0]['display_name'])

        q2 = {
            'filter': '',
            'sort': 'display_name',
            'sortOrder': 'desc',
            'pageNumber': '0',
            'pageSize': '20'
        }
        response = self.searchUsers(query=q2, user=admin_user)

        # users_after2 = db.session.query(User).all()
        # self.assertEqual(len(users_after2), 3)

        self.assertEqual(normal_user.display_name,
                         response['items'][0]['display_name'])

    def test_admin_owner_should_be_able_to_view_their_own_resources(self):
        institution = self.construct_institution(
            name="University of Galactic Domination",
            domain="empire.galaxy.gov")

        u = self.construct_admin_user(
            eppn="emperor@empire.galaxy.gov",
            display_name="Emperor Palpatine",
            email="emperor@empire.galaxy.gov",
            institution=institution)

        resources = self.construct_various_resources(
            institution=institution, owner=u.email)
        self.assertEqual(16, len(resources))

        rv = self.app.get(
            '/api/resource',
            query_string={'limit': '16'},
            follow_redirects=True,
            content_type="application/json",
            headers=self.logged_in_headers(user=u))
        self.assertSuccess(rv)
        result = json.loads(rv.get_data(as_text=True))

        # General user owns 8 of the 16 resources, half of
        # which are from a different institution.
        # They can see all but the 2 private resources from
        # a different institution that they don't own.
        self.assertEqual(14, len(result))

        # Search endpoint should return the same number of results
        search_results = self.search(query={}, user=u)
        self.assertEqual(len(result), search_results['total'])
