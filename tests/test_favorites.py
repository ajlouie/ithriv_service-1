import json

from tests.base_test import BaseTest
from app import db
from app.models import User


class TestFavorites(BaseTest):
    def test_add_favorite(self):
        self.construct_various_users()

        r = self.construct_resource()
        u = User.query.filter_by(eppn=self.test_eppn).first()
        favorite_data = {"resource_id": r.id, "user_id": u.id}

        rv = self.app.post(
            '/api/favorite',
            data=json.dumps(favorite_data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(u.id, response["user_id"])
        self.assertEqual(r.id, response["resource_id"])
        self.assertEqual(1, len(r.favorites))

    def test_remove_favorite(self):
        self.test_add_favorite()
        rv = self.app.get(
            '/api/favorite/%i' % 1, content_type="application/json")
        self.assertSuccess(rv)
        rv = self.app.delete('/api/favorite/%i' % 1)
        self.assertSuccess(rv)
        rv = self.app.get(
            '/api/favorite/%i' % 1, content_type="application/json")
        self.assertEqual(404, rv.status_code)

    def test_delete_resource_deletes_favorite(self):
        r = self.construct_resource()
        u = self.construct_user(display_name="Oscar the Grouch")

        favorite_data = {"resource_id": r.id, "user_id": u.id}

        rv = self.app.post(
            '/api/favorite',
            data=json.dumps(favorite_data),
            content_type="application/json")
        self.assertSuccess(rv)
        self.assertEqual(1, len(r.favorites))

        rv = self.app.delete(
            '/api/resource/1',
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)

        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertEqual(404, rv.status_code)

        rv = self.app.get('/api/favorite/1', content_type="application/json")
        self.assertEqual(404, rv.status_code)

    def test_user_favorites_list(self):
        r1 = self.construct_resource(name="Birdseed sale at Hooper's")
        r2 = self.construct_resource(name="Slimy the worm's flying school")
        r3 = self.construct_resource(name="Oscar's Trash Orchestra")
        u1 = User(
            id=1,
            eppn=self.test_eppn,
            display_name="Oscar the Grouch",
            email="oscar@sesamestreet.com")
        u2 = User(
            id=2,
            eppn=self.admin_eppn,
            display_name="Big Bird",
            email="bigbird@sesamestreet.com")

        db.session.commit()

        favorite_data_u1 = [
            {
                "resource_id": r2.id
            },
            {
                "resource_id": r3.id
            },
        ]

        favorite_data_u2 = [
            {
                "resource_id": r1.id
            },
            {
                "resource_id": r2.id
            },
            {
                "resource_id": r3.id
            },
        ]

        # Creating Favorites and testing that the correct amount
        # show up for the correct user
        rv = self.app.post(
            '/api/session/favorite',
            data=json.dumps(favorite_data_u1),
            content_type="application/json",
            headers=self.logged_in_headers(user=u1),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(2, len(response))

        rv = self.app.post(
            '/api/session/favorite',
            data=json.dumps(favorite_data_u2),
            content_type="application/json",
            headers=self.logged_in_headers(user=u2),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(3, len(response))

        # Testing to see that favorites are not viewable when logged out
        rv = self.app.get(
            '/api/session/favorite', content_type="application/json")
        self.assertEqual(401, rv.status_code)
