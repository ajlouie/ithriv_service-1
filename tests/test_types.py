import json

from tests.base_test import BaseTest
from app import db
from app.models import ThrivType


class TestTypes(BaseTest):

    def test_create_type(self):
        r_type = {"name": "A typey typer type"}
        rv = self.app.post(
            '/api/type',
            data=json.dumps(r_type),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        response["name"] = "A typey typer type"
        self.assertEqual(1, db.session.query(ThrivType).count())

    def test_edit_type(self):
        r_type = ThrivType(name="one way")
        db.session.add(r_type)
        db.session.commit()
        rv = self.app.get(
            '/api/type/%i' % r_type.id, content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        response['name'] = "or another"
        rv = self.app.put(
            '/api/type/%i' % r_type.id,
            data=json.dumps(response),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        response["name"] = "or another"

    def test_delete_type(self):
        r_type = ThrivType(name="one way")
        db.session.add(r_type)
        db.session.commit()
        self.assertEqual(1, db.session.query(ThrivType).count())
        rv = self.app.delete(
            '/api/type/%i' % r_type.id, content_type="application/json")
        self.assertEqual(0, db.session.query(ThrivType).count())

    def test_list_types(self):
        db.session.add(ThrivType(name="a"))
        db.session.add(ThrivType(name="b"))
        db.session.add(ThrivType(name="c"))
        db.session.commit()
        rv = self.app.get('/api/type', content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(3, len(response))
