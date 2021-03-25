import json
from io import BytesIO

from tests.base_test import BaseTest
from app import db
from app.models import Icon, Category, ThrivType
from app.resources.schema import CategorySchema, IconSchema, ThrivTypeSchema


class TestIcons(BaseTest):
    def test_list_category_icons(self):
        i1 = Icon(name="Happy Coconuts")
        i2 = Icon(name="Fly on Strings")
        i3 = Icon(name="Between two Swallows")
        i4 = Icon(name="otherwise unladen")
        db.session.add_all([i1, i2, i3, i4])
        db.session.commit()
        rv = self.app.get('/api/icon', content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(4, len(response))

    def test_update_icon(self):
        i = Icon(name="Happy Coconuts")
        db.session.add(i)
        db.session.commit()
        i.name = "Happier Coconuts"
        rv = self.app.put(
            '/api/icon/%i' % i.id,
            data=json.dumps(IconSchema().dump(i).data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual("Happier Coconuts", i.name)

    def test_upload_icon(self):
        i = {"name": "Happy Coconuts"}
        rv = self.app.post(
            '/api/icon', data=json.dumps(i), content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        icon_id = response["id"]

        rv = self.app.put(
            '/api/icon/%i' % icon_id,
            data=dict(image=(BytesIO(b"hi everyone"), 'test.svg'), ))
        self.assertSuccess(rv)
        data = json.loads(rv.get_data(as_text=True))
        self.assertEqual(
            "https://s3.amazonaws.com/edplatform-ithriv-test-bucket/"
            "ithriv/icon/%i.svg" % icon_id, data["url"])

    def test_set_category_icon(self):
        category = Category(
            name="City Museum",
            description="A wickedly cool amazing place in St Louis",
            color="blue")
        db.session.add(category)
        icon = Icon(name="Cool Places")
        db.session.add(icon)
        db.session.commit()
        category.icon_id = icon.id
        rv = self.app.post(
            '/api/category',
            data=json.dumps(CategorySchema().dump(category).data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(icon.id, response["icon_id"])
        self.assertEqual("Cool Places", response["icon"]["name"])

    def test_set_type_icon(self):
        thrivtype = ThrivType(name="Wickedly Cool")
        db.session.add(thrivtype)
        icon = Icon(name="Cool Places")
        db.session.add(icon)
        db.session.commit()
        thrivtype.icon_id = icon.id
        rv = self.app.post(
            '/api/category',
            data=json.dumps(ThrivTypeSchema().dump(thrivtype).data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(icon.id, response["icon_id"])
        self.assertEqual("Cool Places", response["icon"]["name"])
