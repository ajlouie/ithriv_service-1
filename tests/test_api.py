import json

from tests.base_test import BaseTest


class TestApi(BaseTest):
    def test_base_endpoint(self):
        rv = self.app.get(
            '/', follow_redirects=True, content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response['api.categoryendpoint'], '/api/category/<id>')
        self.assertEqual(response['api.categorylistendpoint'], '/api/category')
        self.assertEqual(response['api.institutionendpoint'], '/api/institution/<id>')
        self.assertEqual(response['api.institutionlistendpoint'], '/api/institution')
        self.assertEqual(response['api.resourceendpoint'], '/api/resource/<id>')
        self.assertEqual(response['api.resourcelistendpoint'], '/api/resource')
        self.assertEqual(response['api.sessionendpoint'], '/api/session')
        self.assertEqual(response['api.sessionstatusendpoint'], '/api/session_status')
        self.assertEqual(response['api.userendpoint'], '/api/user/<id>')
        self.assertEqual(response['auth.forgot_password'], '/api/forgot_password')
        self.assertEqual(response['auth.login_password'], '/api/login_password')
        self.assertEqual(response['auth.reset_password'], '/api/reset_password')
