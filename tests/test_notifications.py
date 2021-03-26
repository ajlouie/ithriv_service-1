import json

from tests.base_test import BaseTest
from app.models import NotificationStatus


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

        # Update read/unread status on the notification.
        self.assertEqual(NotificationStatus.unread, response_before['status'])
        rv_status = self.app.post(
            url,
            data=json.dumps({'status': 'read'}),
            content_type="application/json",
            headers=self.logged_in_headers(user=user),
            follow_redirects=True,

        )
        self.assertSuccess(rv_status)

        rv_after_status = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=user),
            content_type="application/json")
        self.assertSuccess(rv_after_status)
        response_after_status = json.loads(rv_after_status.get_data(as_text=True))
        self.assertEqual(NotificationStatus.read, response_after_status['status'])

        # Take action on the notification.
        url_action = url + f'/action/{a1.id}'
        print('url_action', url_action)
        rv_action = self.app.post(
            url_action,
            content_type="application/json",
            headers=self.logged_in_headers(user=user), follow_redirects=True)
        self.assertSuccess(rv_action)

        rv_after_action = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=user),
            content_type="application/json")
        self.assertSuccess(rv_after_action)
        response_after_action = json.loads(rv_after_action.get_data(as_text=True))
        self.assertIsNotNone(response_after_action['action_taken'])
        self.assertEqual(response_after_action['action_taken']['notification_action_id'], a1.id)

    def test_admin_add_and_update_notification_actions(self):
        admin_user = self.construct_admin_user()

        url = f'/api/notification_action'
        rv_all_before_add = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=admin_user),
            content_type="application/json")
        self.assertSuccess(rv_all_before_add)
        response_all_before_add = json.loads(rv_all_before_add.get_data(as_text=True))
        num_actions_before = len(response_all_before_add)

        # Add 2 actions directly to the database.
        a1 = self.construct_action(title='a1', action_type='Approve')
        a2 = self.construct_action(title='a2', action_type='Deny')

        rv_all_after_db_add = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=admin_user),
            content_type="application/json")
        self.assertSuccess(rv_all_after_db_add)
        response_all_after_db_add = json.loads(rv_all_after_db_add.get_data(as_text=True))
        num_after_db_add = len(response_all_after_db_add)
        self.assertEqual(num_after_db_add, num_actions_before + 2)

        # Add an action via the endpoint
        a3_dict = {
            'title': 'Storm the castle',
            'description': 'Buttercup is marry Humperdinck in little less than half an hour.',
            'url': 'https://wuv.twoo.wuv',
            'type': 'Edit',
        }
        rv_after_add = self.app.put(
            url,
            data=json.dumps(a3_dict),
            content_type="application/json",
            headers=self.logged_in_headers(user=admin_user),
            follow_redirects=True,

        )
        self.assertSuccess(rv_after_add)
        response_after_add = json.loads(rv_after_add.get_data(as_text=True))
        self.assertEqual(response_after_add['title'], a3_dict['title'])
        self.assertEqual(response_after_add['description'], a3_dict['description'])
        self.assertEqual(response_after_add['url'], a3_dict['url'])
        self.assertEqual(response_after_add['type'], a3_dict['type'])
        self.assertIsNotNone(response_after_add['id'])
        a3_id = response_after_add['id']

        # There should be one more action now.
        rv_all_after_add = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=admin_user),
            content_type="application/json")
        self.assertSuccess(rv_all_after_add)
        response_all_after_add = json.loads(rv_all_after_add.get_data(as_text=True))
        num_after_add = len(response_all_after_add)
        self.assertEqual(num_after_add, num_after_db_add + 1)

        # Edit action via the endpoint.
        url_action = url + f'/{a3_id}'
        a3_dict['description'] = 'So all we have to do is get in, break up the wedding, steal the princess, ' \
                                 'make our escape... after I kill Count Rugen.'
        rv_after_edit = self.app.post(
            url_action,
            data=json.dumps(a3_dict),
            content_type="application/json",
            headers=self.logged_in_headers(user=admin_user),
            follow_redirects=True
        )
        self.assertSuccess(rv_after_edit)
        response_after_edit = json.loads(rv_after_edit.get_data(as_text=True))
        self.assertEqual(response_after_edit['title'], a3_dict['title'])
        self.assertEqual(response_after_edit['description'], a3_dict['description'])

        # The total number of actions should be the same.
        rv_all_after_edit = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=admin_user),
            content_type="application/json")
        self.assertSuccess(rv_all_after_edit)
        response_all_after_edit = json.loads(rv_all_after_edit.get_data(as_text=True))
        num_after_edit = len(response_all_after_edit)
        self.assertEqual(num_after_edit, num_after_add)

    def test_delete_notification_actions(self):
        admin_user = self.construct_admin_user()

        # Add 2 actions directly to the database.
        a1 = self.construct_action(title='a1', action_type='Approve')
        a2 = self.construct_action(title='a2', action_type='Deny')

        url = f'/api/notification_action'
        rv_all_before_delete = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=admin_user),
            content_type="application/json")
        self.assertSuccess(rv_all_before_delete)
        response_all_before_delete = json.loads(rv_all_before_delete.get_data(as_text=True))
        num_actions_before = len(response_all_before_delete)

        # Delete the first action.
        url_action = url + f'/{a1.id}'
        rv_after_delete = self.app.delete(
            url_action,
            content_type="application/json",
            headers=self.logged_in_headers(user=admin_user),
            follow_redirects=True)
        self.assertSuccess(rv_after_delete)

        # Should return 404 now for the first action.
        rv_get_after_delete = self.app.get(
            url_action,
            content_type="application/json",
            headers=self.logged_in_headers(user=admin_user),
            follow_redirects=True)
        self.assertEqual(404, rv_get_after_delete.status_code)

        # There should be one fewer actions.
        rv_all_after_delete = self.app.get(
            url,
            follow_redirects=True,
            headers=self.logged_in_headers(user=admin_user),
            content_type="application/json")
        self.assertSuccess(rv_all_after_delete)
        response_all_after_delete = json.loads(rv_all_after_delete.get_data(as_text=True))
        num_actions_after = len(response_all_after_delete)
        self.assertEqual(num_actions_after, num_actions_before - 1)

