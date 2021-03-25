import json

from tests.base_test import BaseTest
from app import db
from app.models import User


class TestApprovals(BaseTest):
    def test_approved_resources_list_with_general_users(self):
        big_bird = self.construct_user(
            id=123,
            display_name="Big Bird",
            email="bigbird@sesamestreet.com",
            eppn="bigbird@sesamestreet.com")
        oscar = self.construct_user(
            id=456,
            display_name="Oscar",
            email="oscar@sesamestreet.com",
            eppn="oscar@sesamestreet.com")
        grover = self.construct_user(
            id=789,
            display_name="Grover",
            email="grover@sesamestreet.com",
            eppn="grover@sesamestreet.com")

        self.construct_resource(
            name="Birdseed sale at Hooper's",
            owner=big_bird.email,
            approved="Approved")
        self.construct_resource(
            name="Slimy the worm's flying school",
            owner=oscar.email + "; " + big_bird.email,
            approved="Approved")
        self.construct_resource(
            name="Oscar's Trash Orchestra",
            owner=oscar.email,
            approved="Unapproved")
        self.construct_resource(
            name="Snuffy's Balloon Collection",
            owner=oscar.email + " " + big_bird.email,
            approved="Unapproved")

        # Testing that the correct amount of resources show up
        # for the correct user. Oscar should see all four
        # resources -- the three he owns and the Approved
        # one he doesn't
        rv = self.app.get(
            '/api/resource',
            content_type="application/json",
            headers=self.logged_in_headers(user=oscar),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(4, len(response))

        # Big Bird should see the three resources he owns, and
        # not the Unapproved one he doesn't
        rv = self.app.get(
            '/api/resource',
            content_type="application/json",
            headers=self.logged_in_headers(user=big_bird),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(3, len(response))

        # Grover should see the two approved resources and nothing else
        rv = self.app.get(
            '/api/resource',
            content_type="application/json",
            headers=self.logged_in_headers(user=grover),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(2, len(response))

    def test_approved_resources_list_with_admin_user(self):
        self.construct_resource(
            name="Birdseed sale at Hooper's",
            owner="bigbird@sesamestreet.com",
            approved="Approved")
        self.construct_resource(
            name="Slimy the worm's flying school",
            owner="oscar@sesamestreet.com; "
                  "bigbird@sesamestreet.com",
            approved="Approved")
        self.construct_resource(
            name="Oscar's Trash Orchestra",
            owner="oscar@sesamestreet.com",
            approved="Unapproved")
        self.construct_resource(
            name="Snuffy's Balloon Collection",
            owner="oscar@sesamestreet.com "
                  "bigbird@sesamestreet.com",
            approved="Unpproved")
        u1 = User(
            id=4,
            eppn='maria@seseme.edu',
            display_name="Maria",
            email="maria@sesamestreet.com",
            role="Admin")
        db.session.add(u1)
        db.session.commit()

        # Maria should see all the resources as an Admin
        rv = self.app.get(
            '/api/resource',
            content_type="application/json",
            headers=self.logged_in_headers(user=u1),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(4, len(response))

    def test_approved_resources_list_with_no_user(self):
        self.construct_resource(
            name="Birdseed sale at Hooper's",
            owner="bigbird@sesamestreet.com",
            approved="Approved")
        self.construct_resource(
            name="Slimy the worm's flying school",
            owner="oscar@sesamestreet.com; "
                  "bigbird@sesamestreet.com",
            approved="Approved")
        self.construct_resource(
            name="Oscar's Trash Orchestra",
            owner="oscar@sesamestreet.com",
            approved="Unapproved")
        self.construct_resource(
            name="Snuffy's Balloon Collection",
            owner="oscar@sesamestreet.com "
                  "bigbird@sesamestreet.com",
            approved="Unapproved")

        # When there is no user logged in, they should only see
        # the two approved resources
        rv = self.app.get('/api/resource', content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(2, len(response))
