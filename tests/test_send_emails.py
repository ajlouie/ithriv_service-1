import json

from tests.base_test import BaseTest
from app.email_service import TEST_MESSAGES
from app.models import EmailLog


class TestSendEmails(BaseTest):
    def test_register_sends_email(self):
        message_count = len(TEST_MESSAGES)
        self.test_create_user_with_password()
        self.assertGreater(len(TEST_MESSAGES), message_count)
        self.assertEqual("iTHRIV: Confirm Email",
                         self.decode(TEST_MESSAGES[-1]['subject']))

        logs = EmailLog.query.all()
        self.assertIsNotNone(logs[-1].tracking_code)

    def test_forgot_password_sends_email(self, display_name="Gemma Whelan", eppn="yara-greyjoy@got.com",
                                       email="yara-greyjoy@got.com", role="User", password="AshaKraken"):
        user = self.test_create_user_with_password(display_name=display_name, eppn=eppn,
                                       email=email, role=role, password=password)
        message_count = len(TEST_MESSAGES)
        data = {"email": user.email}
        rv = self.app.post(
            '/api/forgot_password',
            data=json.dumps(data),
            content_type="application/json")
        self.assertSuccess(rv)
        self.assertGreater(len(TEST_MESSAGES), message_count)
        self.assertEqual("iTHRIV: Password Reset Email",
                         self.decode(TEST_MESSAGES[-1]['subject']))

        logs = EmailLog.query.all()
        self.assertIsNotNone(logs[-1].tracking_code)

    def test_consult_request_sends_email(self):
        # This test will send two emails. One confirming
        # that the user is created:
        user = self.test_create_user_with_password()
        message_count = len(TEST_MESSAGES)
        data = {"user_id": user.id}
        # ...And a second email requesting the consult:
        rv = self.app.post(
            '/api/consult_request',
            data=json.dumps(data),
            headers=self.logged_in_headers(user),
            content_type="application/json")
        self.assertSuccess(rv)
        self.assertGreater(len(TEST_MESSAGES), message_count)
        self.assertEqual("iTHRIV: Consult Request",
                         self.decode(TEST_MESSAGES[-1]['subject']))

        logs = EmailLog.query.all()
        self.assertIsNotNone(logs[-1].tracking_code)

    def test_approval_request_sends_email(self):
        # This test will send three emails.
        # 1. First email confirms that the user is created:
        user = self.construct_user()
        admin_user = self.construct_admin_user()
        message_count = len(TEST_MESSAGES)

        # Create the resource
        resource = self.construct_resource()

        data = {"user_id": user.id, "resource_id": resource.id}

        # Request approval
        rv = self.app.post(
            '/api/approval_request',
            data=json.dumps(data),
            headers=self.logged_in_headers(user=user),
            content_type="application/json")
        self.assertSuccess(rv)
        self.assertGreater(len(TEST_MESSAGES), message_count)
        logs = EmailLog.query.all()

        # 2. Second email goes to the admin requesting approval:
        self.assertEqual("iTHRIV: Resource Approval Request",
                         self.decode(TEST_MESSAGES[-2]['Subject']))
        self.assertEqual(admin_user.email, TEST_MESSAGES[-2]['To'])
        self.assertIsNotNone(logs[-2].tracking_code)

        # 3. Third email goes to the user confirming
        # receipt of the approval request:
        self.assertEqual("iTHRIV: Resource Approval Request Confirmed",
                         self.decode(TEST_MESSAGES[-1]['Subject']))
        self.assertEqual(user.email, TEST_MESSAGES[-1]['To'])
        self.assertIsNotNone(logs[-1].tracking_code)

