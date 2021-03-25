from tests.base_test import BaseTest
from app import elastic_index, db
from app.models import ThrivResource


class TestSearch(BaseTest):
    def test_search_crud(self):
        rainbow_query = {'query': 'rainbows', 'filters': []}
        world_query = {'query': 'world', 'filters': []}
        search_results = self.search(rainbow_query)
        self.assertEqual(0, len(search_results["resources"]))
        search_results = self.search(world_query)
        self.assertEqual(0, len(search_results["resources"]))

        resource = self.construct_resource(
            name='space unicorn', description="delivering rainbows")
        elastic_index.add_resource(resource)
        search_results = self.search(rainbow_query)
        self.assertEqual(1, len(search_results["resources"]))
        self.assertEqual(search_results['resources'][0]['id'], resource.id)
        search_results = self.search(world_query)
        self.assertEqual(0, len(search_results["resources"]))

        resource.description = 'all around the world'
        elastic_index.update_resource(resource)

        search_results = self.search(rainbow_query)
        self.assertEqual(0, len(search_results["resources"]))
        search_results = self.search(world_query)
        self.assertEqual(1, len(search_results["resources"]))
        self.assertEqual(resource.id, search_results['resources'][0]['id'])

        elastic_index.remove_resource(resource)
        search_results = self.search(rainbow_query)
        self.assertEqual(0, len(search_results["resources"]))
        search_results = self.search(world_query)
        self.assertEqual(0, len(search_results["resources"]))

    def test_search_resource_by_name(self):
        resource = self.construct_resource(name="space kittens")
        data = {'query': 'kittens', 'filters': []}
        search_results = self.search(data)
        self.assertEqual(1, len(search_results["resources"]))

    def test_search_unapproved_resource(self):
        # Unapproved resources should only appear in
        # search results for Admin users
        r = self.construct_resource(
            name="space kittens", approved="Unapproved")
        query = {'query': 'kittens', 'filters': []}

        # Anonymous user gets 0 results
        results_anon = self.search_anonymous(query)
        self.assertEqual(0, len(results_anon["resources"]))

        # Admin user gets 1 result
        results_admin = self.search(query)
        self.assertEqual(1, len(results_admin["resources"]))

    def test_search_resource_by_description(self):
        r = self.construct_resource(
            name="space kittens", description="Flight of the fur puff")
        data = {'query': 'fur puff', 'filters': []}
        search_results = self.search(data)
        self.assertEqual(1, len(search_results["resources"]))

    def test_search_resource_by_website(self):
        resource = self.construct_resource(website="www.stuff.edu")
        data = {'query': 'www.stuff.edu', 'filters': []}
        search_results = self.search(data)
        self.assertEqual(1, len(search_results["resources"]))

    def test_search_resource_by_owner(self):
        resource = self.construct_resource(owner="Mr. McDoodle Pants")
        data = {'query': 'McDoodle', 'filters': []}
        search_results = self.search(data)
        self.assertEqual(1, len(search_results["resources"]))

    def test_search_filters(self):
        r = self.construct_resource(
            type_name="hgttg",
            description="There is a theory which "
                        "states that if ever anyone discovers exactly what "
                        "the Universe is for and why it is here, it will "
                        "instantly disappear and be replaced by something "
                        "even more bizarre and inexplicable. There is another "
                        "theory which states that this has already happened.")
        data = {'query': '', 'filters': [{'field': 'Type', 'value': 'hgttg'}]}

        search_results = self.search(data)
        self.assertEqual(1, len(search_results["resources"]))

    def test_search_filter_on_approval(self):
        r = self.construct_resource(
            type_name="Woods",
            description="A short trip on the river.",
            approved="Approved")
        data = {
            'query': '',
            'filters': [{
                'field': 'Approved',
                'value': "Approved"
            }]
        }
        search_results = self.search(data)
        self.assertEqual(1, len(search_results["resources"]))

    def test_search_facet_counts(self):
        r1 = self.construct_resource(
            type_name="hgttg",
            name="Golgafrinchan Ark Fleet Ship B",
            description="There is a theory which states that if ever "
                        "anyone discovers exactly what the Universe is "
                        "for and why it is here, it will instantly "
                        "disappear and be replaced by something even more "
                        "bizarre and inexplicable. There is another "
                        "theory which states that this has already "
                        "happened.")
        r2 = self.construct_resource(
            type_name="brazil",
            name="Spoor and Dowser",
            description="Information Transit got the wrong man. I got the "
                        "*right* man. The wrong one was delivered to me "
                        "as the right man, I accepted him on good faith "
                        "as the right man. Was I wrong?")

        db_resources = db.session.query(ThrivResource).all()
        self.assertEqual(2, len(db_resources))

        data = {'query': '', 'filters': []}
        search_results = self.search(data)
        self.assertEqual(2, len(search_results["resources"]))
        self.assertTrue("facets" in search_results)
        self.assertEqual(3, len(search_results["facets"]))
        self.assertTrue("facetCounts" in search_results["facets"][0])
        self.assertTrue(
            "category" in search_results["facets"][0]["facetCounts"][0])
        self.assertTrue(
            "hit_count" in search_results["facets"][0]["facetCounts"][0])
        self.assertTrue(
            "is_selected" in search_results["facets"][0]["facetCounts"][0])
