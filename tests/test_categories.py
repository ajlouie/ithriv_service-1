import json

from tests.base_test import BaseTest
from app import db
from app.models import ResourceCategory, Category
from app.resources.schema import CategorySchema


class TestCategories(BaseTest):
    def test_category_basics(self):
        category = self.construct_category()
        rv = self.app.get(
            '/api/category/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["id"], 1)
        self.assertEqual(response["name"], 'Test Category')
        self.assertEqual(response["description"], 'A category to test with!')

    def test_create_category(self):
        c = {
            "name": "Old bowls",
            "description": "Funky bowls of yuck still on my desk. Ews!",
            "color": "#000",
            "brief_description": "Funky Bowls!",
            "image": "image.png"
        }
        rv = self.app.post(
            '/api/category',
            data=json.dumps(c),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(c["name"], response["name"])
        self.assertEqual(c["description"], response["description"])
        self.assertEqual(c["brief_description"], response["brief_description"])
        self.assertEqual(c["color"], response["color"])
        self.assertEqual(c["image"], response["image"])

    def test_create_child_category(self):
        parent = Category(
            name="Desk Stuffs", description="The many stuffs on my desk")
        db.session.add(parent)
        db.session.commit()
        c = {
            "name": "Old bowls",
            "description": "Funky bowls of yuck still on my desk. Ews!",
            "parent_id": parent.id
        }
        rv = self.app.post(
            '/api/category',
            data=json.dumps(c),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(parent.id, response["parent"]["id"])
        self.assertEqual(0, response["parent"]["level"])
        self.assertEqual(1, response["level"])

    def test_update_category(self):
        c = Category(
            name="Desk Stuffs",
            description="The many stuffs on my desk",
            color="#ABC222")
        db.session.add(c)
        db.session.commit()
        c.description = "A new better description of the crap all over my " \
                        "desk right now.  It's a mess."
        rv = self.app.put(
            '/api/category/%i' % c.id,
            data=json.dumps(CategorySchema().dump(c).data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(c.description, response["description"])

    def test_category_depth_is_limited(self):
        c1 = self.construct_category()
        c2 = self.construct_category(
            name="I'm the kid", description="A Child Category", parent=c1)
        c3 = self.construct_category(
            name="I'm the grand kid",
            description="A Child Category",
            parent=c2)
        c4 = self.construct_category(
            name="I'm the great grand kid",
            description="A Child Category",
            parent=c3)

        rv = self.app.get(
            '/api/category',
            follow_redirects=True,
            content_type="application/json")

        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))

        self.assertEqual(1, len(response))
        self.assertEqual(1, len(response[0]["children"]))

    def test_list_categories(self):
        self.construct_category(
            name="c1", description="c1 description", parent=None)
        self.construct_category(
            name="c2", description="c2 description", parent=None)
        self.construct_category(
            name="c3", description="c3 description", parent=None)

        rv = self.app.get(
            '/api/category',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response[0]['name'], 'c1')
        self.assertEqual(response[1]['name'], 'c2')
        self.assertEqual(response[2]['name'], 'c3')

    def test_list_categories_sorts_in_display_order(self):
        self.construct_category(
            name="M", description="M description", display_order=1)
        self.construct_category(name="O", description="O description")
        self.construct_category(
            name="N", description="N description", display_order=0)
        self.construct_category(name="K", description="K description")
        self.construct_category(
            name="E", description="E description", display_order=2)
        self.construct_category(name="Y", description="Y description")

        rv = self.app.get(
            '/api/category',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))

        # Items with an explicit display order are listed first
        self.assertEqual(response[0]['name'], 'N')
        self.assertEqual(response[1]['name'], 'M')
        self.assertEqual(response[2]['name'], 'E')

        # Items with same display order are sorted by name
        self.assertEqual(response[3]['name'], 'K')
        self.assertEqual(response[4]['name'], 'O')
        self.assertEqual(response[5]['name'], 'Y')

    def test_list_root_categories(self):
        self.construct_category(
            name="c1", description="c1 description", parent=None)
        self.construct_category(
            name="c2", description="c2 description", parent=None)
        self.construct_category(
            name="c3", description="c3 description", parent=None)

        rv = self.app.get(
            '/api/category/root',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response[0]['name'], 'c1')
        self.assertEqual(response[1]['name'], 'c2')
        self.assertEqual(response[2]['name'], 'c3')

    def test_list_root_categories_sorts_in_display_order(self):
        self.construct_category(
            name="Z", description="Z description", display_order=1)
        self.construct_category(name="O", description="O description")
        self.construct_category(
            name="M", description="M description", display_order=0)
        self.construct_category(name="B", description="B description")
        self.construct_category(
            name="I", description="I description", display_order=2)
        self.construct_category(name="E", description="E description")

        rv = self.app.get(
            '/api/category/root',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))

        # Items with an explicit display order are listed first
        self.assertEqual(response[0]['name'], 'M')
        self.assertEqual(response[1]['name'], 'Z')
        self.assertEqual(response[2]['name'], 'I')

        # Items with same display order are sorted by name
        self.assertEqual(response[3]['name'], 'B')
        self.assertEqual(response[4]['name'], 'E')
        self.assertEqual(response[5]['name'], 'O')

    def test_category_has_links(self):
        self.construct_category()
        rv = self.app.get(
            '/api/category/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["_links"]["self"], '/api/category/1')
        self.assertEqual(response["_links"]["collection"], '/api/category')

    def test_category_has_children(self):
        c1 = self.construct_category()
        c2 = self.construct_category(
            name="I'm the kid", description="A Child Category", parent=c1)
        rv = self.app.get(
            '/api/category/1',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["children"][0]['id'], 2)
        self.assertEqual(response["children"][0]['name'], "I'm the kid")

    def test_category_has_parents_and_that_parent_has_no_children(self):
        c1 = self.construct_category()
        c2 = self.construct_category(
            name="I'm the kid", description="A Child Category", parent=c1)
        c3 = self.construct_category(
            name="I'm the grand kid",
            description="A Child Category",
            parent=c2)
        rv = self.app.get(
            '/api/category/3',
            follow_redirects=True,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response["parent"]['id'], 2)
        self.assertNotIn("children", response["parent"])

    def test_category_has_parents_color_if_not_set(self):
        parent = Category(
            name="Beer",
            description="There are lots of types of beer.",
            color="#A52A2A")
        db.session.add(parent)
        db.session.commit()
        c = {
            "name": "Old bowls",
            "description": "Funky bowls of yuck still on my desk. Ews!",
            "parent_id": parent.id
        }
        rv = self.app.post(
            '/api/category',
            data=json.dumps(c),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual("#A52A2A", response["color"])

    def test_category_has_ordered_children(self):
        parent = Category(
            name="Beer",
            description="There are lots of types of beer.",
            color="#A52A2A")
        c1 = Category(
            name="Zinger",
            description="Orange flavoered crap beer, served with shame "
                        "and an umbrella",
            parent=parent)
        c2 = Category(
            name="Ale",
            description="Includes the Indian Pale Ale, which comes in "
                        "120,000 different varieties now.",
            parent=parent)
        c3 = Category(
            name="Hefeweizen",
            description="Smells of bananas, best drunk in a German garden",
            parent=parent)

        db.session.add_all([parent, c1, c2, c3])
        db.session.commit()
        rv = self.app.get(
            '/api/category/%i' % parent.id, content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(3, len(response["children"]))
        self.assertEqual("Ale", response["children"][0]["name"])
        self.assertEqual("Hefeweizen", response["children"][1]["name"])
        self.assertEqual("Zinger", response["children"][2]["name"])

    def test_delete_category(self):
        c = self.construct_category()
        self.assertEqual(1, db.session.query(Category).count())
        rv = self.app.delete('/api/category/%i' % c.id)
        self.assertSuccess(rv)
        self.assertEqual(0, db.session.query(Category).count())

    def test_get_resource_by_category(self):
        c = self.construct_category()
        r = self.construct_resource()
        cr = ResourceCategory(resource=r, category=c)
        db.session.add(cr)
        db.session.commit()
        rv = self.app.get(
            '/api/category/%i/resource' % c.id,
            content_type="application/json",
            headers=self.logged_in_headers())
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(1, len(response))
        self.assertEqual(r.id, response[0]["id"])
        self.assertEqual(r.description, response[0]["resource"]["description"])

    def test_get_resource_by_category_includes_category_details(self):
        c = self.construct_category(name="c1")
        c2 = self.construct_category(name="c2")
        r = self.construct_resource()
        cr = ResourceCategory(resource=r, category=c)
        cr2 = ResourceCategory(resource=r, category=c2)
        db.session.add_all([cr, cr2])
        db.session.commit()
        rv = self.app.get(
            '/api/category/%i/resource' % c.id,
            content_type="application/json",
            headers=self.logged_in_headers())
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(r.id, response[0]["id"])
        self.assertEqual(2,
                         len(response[0]["resource"]["resource_categories"]))
        self.assertEqual(
            "c1", response[0]["resource"]["resource_categories"][0]["category"]
            ["name"])

    def test_get_resource_by_category_sorts_by_favorite_count(self):
        u = self.construct_user(
            display_name="Jar Jar Binks", email="jjb@senate.galaxy.gov")
        c = self.construct_category(name="c1")
        r1 = self.construct_resource(name="r1")
        r2 = self.construct_resource(name="r2")
        cr1 = ResourceCategory(resource=r1, category=c)
        cr2 = ResourceCategory(resource=r2, category=c)
        db.session.add_all([cr1, cr2])
        db.session.commit()

        # Should be sorted by name before any resources are favorited
        rv = self.app.get(
            '/api/category/%i/resource' % c.id,
            content_type="application/json",
            headers=self.logged_in_headers())
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual("r1", response[0]["resource"]["name"])

        # Should be sorted by favorite_count now
        favorite = self.construct_favorite(user=u, resource=r2)
        self.assertEqual(r2.id, favorite.resource_id)

        rv = self.app.get(
            '/api/category/%i/resource' % c.id,
            content_type="application/json",
            headers=self.logged_in_headers())
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual("r2", response[0]["resource"]["name"])

    def test_category_resource_count(self):
        c = self.construct_category()
        r = self.construct_resource(approved="Approved")
        cr = ResourceCategory(resource=r, category=c)
        db.session.add(cr)
        db.session.commit()
        rv = self.app.get(
            '/api/category/%i' % c.id, content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(1, response["resource_count"])

    def test_get_category_by_resource(self):
        c = self.construct_category()
        r = self.construct_resource()
        cr = ResourceCategory(resource=r, category=c)
        db.session.add(cr)
        db.session.commit()
        rv = self.app.get(
            '/api/resource/%i/category' % r.id,
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(1, len(response))
        self.assertEqual(c.id, response[0]["id"])
        self.assertEqual(c.description, response[0]["category"]["description"])

    def test_add_category_to_resource(self):
        c = self.construct_category()
        r = self.construct_resource()

        rc_data = {"resource_id": r.id, "category_id": c.id}

        rv = self.app.post(
            '/api/resource_category',
            data=json.dumps(rc_data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(c.id, response["category_id"])
        self.assertEqual(r.id, response["resource_id"])

    def test_set_all_categories_on_resource(self):
        c1 = self.construct_category(name="c1")
        c2 = self.construct_category(name="c2")
        c3 = self.construct_category(name="c3")
        r = self.construct_resource()

        rc_data = [
            {
                "category_id": c1.id
            },
            {
                "category_id": c2.id
            },
            {
                "category_id": c3.id
            },
        ]
        rv = self.app.post(
            '/api/resource/%i/category' % r.id,
            data=json.dumps(rc_data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(3, len(response))

        rc_data = [{"category_id": c1.id}]
        rv = self.app.post(
            '/api/resource/%i/category' % r.id,
            data=json.dumps(rc_data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(1, len(response))

    def test_remove_category_from_resource(self):
        self.test_add_category_to_resource()
        rv = self.app.delete('/api/resource_category/%i' % 1)
        self.assertSuccess(rv)
        rv = self.app.get(
            '/api/resource/%i/category' % 1, content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(0, len(response))

