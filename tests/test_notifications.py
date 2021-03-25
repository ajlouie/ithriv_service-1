import json

from tests.base_test import BaseTest


class TestNotifications(BaseTest):
    def test_get_notification_list(self):
        user = self.construct_user()
        notifications = {
            "a": {"title": "a", "description": "A is for Apple"},
            "b": {"title": "b", "description": "B is for Banana"},
            "c": {"title": "c", "description": "C is for Cherimoya"},
        }

        for k, n in notifications.items():
            n['db_notification'] = self.construct_notification(title=n['title'], description=n['description'], user=user)

        rv = self.app.get(
            f'/api/notification',
            follow_redirects=True,
            headers=self.logged_in_headers(user=user),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(len(response), len(notifications))

        for n in response:
            self.assertTrue(n['title'] in notifications)
            expected = notifications[n['title']]
            self.assertEqual(n['title'], expected['title'])
            self.assertEqual(n['description'], expected['description'])

    def test_get_notification(self):
        n_title = "Get a Miracle from Max"
        n_description = "Hello in there! Hey! What's so important? What you got here that's worth living for?"
        user = self.construct_user()
        n = self.construct_notification(title=n_title, description=n_description, user=user)
        rv = self.app.get(
            f'/api/notification/{n.id}',
            follow_redirects=True,
            headers=self.logged_in_headers(user=user),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["id"], n.id)
        self.assertEqual(response["title"], n_title)
        self.assertEqual(response["description"], n_description)

    def test_update_notification(self):
        user = self.construct_user()
        a1 = self.construct_action(title='a1', action_type='Approve')
        a2 = self.construct_action(title='a2', action_type='Deny')
        n = self.construct_notification(user=user, actions=[a1, a2])
        url = f'/api/notification/{n.id}'
        rv1 = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=user),
            content_type="application/json")
        self.assertSuccess(rv1)
        response_before = json.loads(rv1.get_data(as_text=True))
        self.assertIsNone(response_before['action_taken'])

        url2 = url + f'/action/{a1.id}'
        print('url2', url2)
        rv2 = self.app.post(
            url2,
            content_type="application/json",
            headers=self.logged_in_headers(user=user), follow_redirects=True)
        self.assertSuccess(rv2)

        rv3 = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=user),
            content_type="application/json")
        self.assertSuccess(rv3)
        response_after = json.loads(rv3.get_data(as_text=True))
        self.assertIsNotNone(response_after['action_taken'])
        self.assertEqual(response_after['action_taken']['notification_action_id'], a1.id)

