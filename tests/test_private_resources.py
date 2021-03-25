import json

from tests.base_test import BaseTest


class TestPrivateResources(BaseTest):

    def test_private_resources_for_general_user(self):
        institution = self.construct_institution(
            name="General Leia's Institute for Social Justice",
            domain="resistance.org")
        self.construct_various_resources(institution=institution)

        u = self.construct_user(
            eppn="FN-2187@resistance.org",
            display_name="Finn",
            email="FN-2187@resistance.org",
            institution=institution)

        rv = self.app.get(
            '/api/resource',
            query_string={'limit': '16'},
            follow_redirects=True,
            content_type="application/json",
            headers=self.logged_in_headers(user=u))
        self.assertSuccess(rv)
        result = json.loads(rv.get_data(as_text=True))

        # Should only return 6 approved resources (4 approved non-private,
        # 2 approved private from user's own institution) out of a total
        # 16 resources
        self.assertEqual(6, len(result))

        # Search endpoint should return the same number of results
        search_results = self.search({}, user=u)
        self.assertEqual(len(result), search_results['total'])

    def test_private_resources_listed_for_admin(self):
        institution = self.construct_institution(
            name="Alderaanian Association of Astrological Anthropology",
            domain="alderaan.gov")

        u = self.construct_admin_user(
            eppn="princess.leia@alderaan.gov",
            display_name="Princess Leia Organa",
            email="princess.leia@alderaan.gov",
            institution=institution)

        self.construct_various_resources(institution=institution)

        rv = self.app.get(
            '/api/resource',
            query_string={'limit': '16'},
            follow_redirects=True,
            content_type="application/json",
            headers=self.logged_in_headers(user=u))
        self.assertSuccess(rv)
        result = json.loads(rv.get_data(as_text=True))

        # Should return only 12 out of 16 resources, since 4 are
        # private to a different institution
        self.assertEqual(12, len(result))

        # Search endpoint should return the same number of results
        search_results = self.search({}, user=u)
        self.assertEqual(len(result), search_results['total'])

    def test_private_resources_not_listed_for_anonymous_user(self):
        resources = self.construct_various_resources()
        self.assertEqual(16, len(resources))

        rv = self.app.get(
            '/api/resource',
            query_string={'limit': '16'},
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        result = json.loads(rv.get_data(as_text=True))

        # Should only return 4 approved, non-private resources
        # out of a total 16 resources
        self.assertEqual(4, len(result))

        # Search endpoint should return the same number of results
        search_results = self.search_anonymous({})
        self.assertEqual(len(result), search_results['total'])
