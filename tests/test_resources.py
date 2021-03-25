import json

from tests.base_test import BaseTest
from app import db
from app.models import ThrivResource, ThrivType


class TestResources(BaseTest):

    def test_resource_basics(self):
        r_name = "Speeder Bike"
        r_description = "Thou and I have thirty miles to" \
                        "ride yet ere dinner time."
        self.construct_resource(name=r_name, description=r_description)
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["name"], r_name)
        self.assertEqual(response["description"], r_description)

    def test_modify_resource_basics(self):
        self.construct_resource()
        rv = self.app.get('/api/resource/1', content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        response['name'] = 'Edwarardos Lemonade and Oil Change'
        response['description'] = 'Better fluids for you and your car.'
        response['website'] = 'http://sartography.com'
        response['cost'] = '$.25 or the going rate'
        response['owner'] = 'Daniel GG Dog Da Funk-a-funka'
        orig_date = response['last_updated']
        rv = self.app.put(
            '/api/resource/1',
            data=json.dumps(response),
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)
        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response['name'],
                         'Edwarardos Lemonade and Oil Change')
        self.assertEqual(response['description'],
                         'Better fluids for you and your car.')
        self.assertEqual(response['website'], 'http://sartography.com')
        self.assertEqual(response['cost'], '$.25 or the going rate')
        self.assertEqual(response['owner'], 'Daniel GG Dog Da Funk-a-funka')
        self.assertNotEqual(orig_date, response['last_updated'])

    def test_set_resource_institution(self):
        institution_name = "Billy Bob Thorton's School for" \
                           "mean short men with big heads"
        inst = self.construct_institution(name=institution_name)
        self.construct_resource()
        rv = self.app.get('/api/resource/1', content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        response['institution_id'] = inst.id
        rv = self.app.put(
            '/api/resource/1',
            data=json.dumps(response),
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)
        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response['institution']['name'], institution_name)
        self.assertEqual(response['institution_id'], inst.id)

    def test_set_resource_type(self):
        self.construct_resource()
        type = ThrivType(name="A sort of greenish purple apricot like thing. ")
        db.session.add(type)
        db.session.commit()
        rv = self.app.get('/api/resource/1', content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        response['type_id'] = type.id
        rv = self.app.put(
            '/api/resource/1',
            data=json.dumps(response),
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)
        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response['type']['name'],
                         "A sort of greenish purple apricot like thing. ")
        self.assertEqual(response['type_id'], type.id)

    def test_delete_resource(self):
        r = self.construct_resource()
        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertSuccess(rv)

        rv = self.app.delete(
            '/api/resource/1',
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)

        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertEqual(404, rv.status_code)

    def test_user_edit_resource(self):
        u1 = self.construct_user(
            eppn="peter@cottontail",
            display_name="Peter Cottontail",
            email="peter@cottontail")
        u2 = self.construct_admin_user(
            eppn="rabbit@velveteen.com",
            display_name="The Velveteen Rabbit",
            email="rabbit@velveteen.com")
        r1 = self.construct_resource(owner=u1.email)
        r2 = self.construct_resource(owner="flopsy@cottontail.com")

        rv = self.app.get('/api/resource/1', content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        response['name'] = 'Farm Fresh Carrots'
        response['owner'] = 'peter@cottontail, flopsy@cottontail.com'
        orig_date = response['last_updated']

        # Peter should be able to edit his own resource
        rv = self.app.put(
            '/api/resource/1',
            data=json.dumps(response),
            content_type="application/json",
            headers=self.logged_in_headers(user=u1),
            follow_redirects=True)
        self.assertSuccess(rv)
        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response['name'], 'Farm Fresh Carrots')
        self.assertEqual(response['owner'],
                         'peter@cottontail, flopsy@cottontail.com')
        self.assertNotEqual(orig_date, response['last_updated'])

        # But Peter should not be able to edit anyone else's resources.
        rv = self.app.get('/api/resource/2', content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        response['name'] = 'Farm Fresh Carrots'
        response['owner'] = 'peter@cottontail, flopsy@cottontail.com'
        orig_date = response['last_updated']
        rv = self.app.put(
            '/api/resource/2',
            data=json.dumps(response),
            content_type="application/json",
            headers=self.logged_in_headers(user=u1),
            follow_redirects=True)
        self.assertEqual(400, rv.status_code)

        # The Velveteen Rabbit can edit others' resources though, as an Admin:
        rv = self.app.get('/api/resource/2', content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        response['name'] = 'All the Carrots and Love'
        response['owner'] = 'rabbit@velveteen.com,' \
                            'peter@cottontail,' \
                            'flopsy@cottontail.com'
        rv = self.app.put(
            '/api/resource/2',
            data=json.dumps(response),
            content_type="application/json",
            headers=self.logged_in_headers(user=u2),
            follow_redirects=True)
        self.assertSuccess(rv)

    def test_general_user_delete_resource(self):
        u1 = self.construct_user(
            eppn="peter@cottontail",
            display_name="Peter Cottontail",
            email="peter@cottontail",
            role="User")
        r1 = self.construct_resource(owner=u1.email)
        r2 = self.construct_resource(owner="flopsy@cottontail.com")
        db.session.add_all([r1, r2])
        db.session.commit()

        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertSuccess(rv)

        rv = self.app.get('/api/resource/2', content_type="application/json")
        self.assertSuccess(rv)
        self.assertEqual(2, db.session.query(ThrivResource).count())

        # We shouldn't be able to delete a resource when not logged in
        rv = self.app.delete(
            '/api/resource/1', content_type="application/json")
        self.assertEqual(401, rv.status_code)
        self.assertEqual(2, db.session.query(ThrivResource).count())

        # A general user should be able to delete their own resources
        rv = self.app.delete(
            '/api/resource/1',
            content_type="application/json",
            headers=self.logged_in_headers(user=u1),
            follow_redirects=True)
        self.assertSuccess(rv)

        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertEqual(404, rv.status_code)
        self.assertEqual(1, db.session.query(ThrivResource).count())

        # And a user shouldn't be able to delete a resource that doesn't
        # belong to them (Flopsy might not want Peter deleting that thing)
        rv = self.app.delete(
            '/api/resource/2',
            content_type="application/json",
            headers=self.logged_in_headers(user=u1),
            follow_redirects=True)
        self.assertEqual(400, rv.status_code)

        rv = self.app.get('/api/resource/2', content_type="application/json")
        self.assertSuccess(rv)
        self.assertEqual(1, db.session.query(ThrivResource).count())

    def test_admin_user_delete_resource(self):
        # Remember -- A user shouldn't be able to delete a resource that
        # doesn't belong to them...
        # ...Unless that user is a superuser, in which case they can delete
        # whatever they want (The Velveteen Rabbit is all-powerful)
        r1 = self.construct_resource(owner="mopsy@cottontail.com")
        u = self.construct_user(
            id=2,
            eppn="rabbit@velveteen.com",
            display_name="The Velveteen Rabbit",
            email="rabbit@velveteen.com",
            role="Admin")

        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertSuccess(rv)
        self.assertEqual(1, db.session.query(ThrivResource).count())

        rv = self.app.delete(
            '/api/resource/1',
            content_type="application/json",
            headers=self.logged_in_headers(user=u),
            follow_redirects=True)
        self.assertSuccess(rv)

        rv = self.app.get('/api/resource/1', content_type="application/json")
        self.assertEqual(404, rv.status_code)
        self.assertEqual(0, db.session.query(ThrivResource).count())

    def test_create_resource(self):
        resource = {
            'name': "Barbarella's Funky Gun",
            'description': "A thing. In a movie, or something."
        }
        rv = self.app.post(
            '/api/resource',
            data=json.dumps(resource),
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response['name'], 'Barbarella\'s Funky Gun')
        self.assertEqual(response['description'],
                         'A thing. In a movie, or something.')
        self.assertEqual(response['id'], 1)

    def test_resource_add_search(self):
        data = {'query': "Flash Gordon", 'filters': []}
        search_results = self.search(data)
        self.assertEqual(0, len(search_results["resources"]))

        resource = {
            'name': "Flash Gordon's zippy ship",
            'description': "Another thing. In a movie, or something."
        }
        rv = self.app.post(
            '/api/resource',
            data=json.dumps(resource),
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)

        search_results = self.search(data)
        self.assertEqual(1, len(search_results["resources"]))

    def test_resource_delete_search(self):
        data = {'query': "Flash Gordon", 'filters': []}
        resource = {
            'name': "Flash Gordon's zippy ship",
            'description': "Another thing. In a movie, or something."
        }

        search_results = self.search(data)
        self.assertEqual(0, len(search_results["resources"]))

        rv = self.app.post(
            '/api/resource',
            data=json.dumps(resource),
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        resource_id = response['id']

        search_results = self.search(data)
        self.assertEqual(1, len(search_results["resources"]))

        rv = self.app.delete(
            '/api/resource/{}'.format(resource_id),
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)

        search_results = self.search(data)
        self.assertEqual(0, len(search_results["resources"]))

    def test_resource_modify_search(self):
        resource = self.construct_resource(
            name="Flash Gordon's zappy raygun",
            description="Yet another thing. In a movie, or something.")
        zappy_query = {'query': 'zappy', 'filters': []}
        zorpy_query = {'query': 'zorpy', 'filters': []}
        search_results = self.search(zappy_query)
        self.assertEqual(1, len(search_results["resources"]))
        search_results = self.search(zorpy_query)
        self.assertEqual(0, len(search_results["resources"]))

        rv = self.app.get('/api/resource/1', content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response['name'], "Flash Gordon's zappy raygun")
        response['name'] = "Flash Gordon's zorpy raygun"
        rv = self.app.put(
            '/api/resource/1',
            data=json.dumps(response),
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)

        search_results = self.search(zappy_query)
        self.assertEqual(0, len(search_results["resources"]))
        search_results = self.search(zorpy_query)
        self.assertEqual(1, len(search_results["resources"]))

    def test_resource_has_approval(self):
        resource = self.construct_resource()
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["approved"], 'Unapproved')
        response["approved"] = 'Approved'
        rv = self.app.put(
            '/api/resource/%i' % 1,
            data=json.dumps(response),
            content_type="application/json",
            headers=self.logged_in_headers(),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["approved"], 'Approved')

    def test_resource_has_availability(self):
        self.construct_resource(owner="Mac Daddy Test", available_to="UVA")
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertIsNotNone(response["availabilities"])
        self.assertIsNotNone(response["availabilities"][0])
        self.assertEqual(True, response["availabilities"][0]["available"])
        self.assertEqual("UVA",
                         response["availabilities"][0]["institution"]["name"])

    def test_resource_has_links(self):
        self.construct_resource()
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["_links"]["self"], '/api/resource/1')
        self.assertEqual(response["_links"]["collection"], '/api/resource')

    def test_resource_has_type(self):
        type_name = "Human-Cyborg Relations"
        self.construct_resource(type=type_name)
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["type"]["name"], type_name)

    def test_proper_error_on_no_resource(self):
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["code"], "not_found")

    def test_resource_has_institution(self):
        institution_name = "Hoth Center for Limb Reconstruction"
        institution = self.construct_institution(name=institution_name)
        self.construct_resource(institution=institution)
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["institution"]["name"], institution_name)

    def test_resource_has_website(self):
        self.construct_resource(website='testy.edu')
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["website"], 'testy.edu')

    def test_resource_has_owner(self):
        self.construct_resource(owner="Mac Daddy Test")
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["owner"], 'Mac Daddy Test')

    def test_resource_has_contact_information(self):
        self.construct_resource(
            contact_email='thor@disney.com',
            contact_phone='555-123-4321',
            contact_notes='Valhala calling!')
        rv = self.app.get(
            '/api/resource/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["contact_email"], 'thor@disney.com')
        self.assertEqual(response["contact_phone"], '555-123-4321')
        self.assertEqual(response["contact_notes"], 'Valhala calling!')

    def test_resource_list_limits_to_10_by_default(self):
        for i in range(20):
            self.construct_resource()
        rv = self.app.get(
            '/api/resource',
            follow_redirects=True,
            content_type="application/json",
            headers=self.logged_in_headers())
        self.assertSuccess(rv)
        result = json.loads(rv.get_data(as_text=True))
        self.assertEqual(10, len(result))

        rv = self.app.get(
            '/api/resource',
            follow_redirects=True,
            query_string={'limit': '5'},
            content_type="application/json",
            headers=self.logged_in_headers())
        self.assertSuccess(rv)
        result = json.loads(rv.get_data(as_text=True))
        self.assertEqual(5, len(result))

    def test_my_resources_list(self):
        # Testing that the resource owner is correctly split
        # with ; , or spaces between email addresses
        self.construct_resource(
            name="Birdseed sale at Hooper's", owner="bigbird@sesamestreet.com")
        self.construct_resource(
            name="Slimy the worm's flying school",
            owner="oscar@sesamestreet.com; "
                  "bigbird@sesamestreet.com")
        self.construct_resource(
            name="Oscar's Trash Orchestra",
            owner="oscar@sesamestreet.com, "
                  "bigbird@sesamestreet.com")
        self.construct_resource(
            name="Snuffy's Balloon Collection",
            owner="oscar@sesamestreet.com "
                  "bigbird@sesamestreet.com")
        u1 = self.construct_user(
            role="User",
            display_name="Oscar the Grouch",
            email="oscar@sesamestreet.com",
            eppn="oscar@sesamestreet.com")
        u2 = self.construct_admin_user(
            role="Admin",
            display_name="Big Bird",
            email="bigbird@sesamestreet.com",
            eppn="bigbird@sesamestreet.com")

        # Testing that the correct amount of user-owned resources
        # show up for the correct user
        rv = self.app.get(
            '/api/session/resource',
            content_type="application/json",
            headers=self.logged_in_headers(user=u1),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(3, len(response))

        rv = self.app.get(
            '/api/session/resource',
            content_type="application/json",
            headers=self.logged_in_headers(user=u2),
            follow_redirects=True)
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(4, len(response))

        # Testing to see that user-owned resources are not
        # viewable when logged out
        rv = self.app.get(
            '/api/session/resource', content_type="application/json")
        self.assertEqual(401, rv.status_code)
