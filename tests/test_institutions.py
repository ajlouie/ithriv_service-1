import json

from tests.base_test import BaseTest
from app import db
from app.models import ThrivInstitution


class TestInstitutions(BaseTest):
    def test_create_institution(self):
        institution = {
            "name": "Ender's Academy for wayward space boys",
            "description": "A school, in outerspace, with weightless games"
        }
        rv = self.app.post(
            '/api/institution',
            data=json.dumps(institution),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(response['name'],
                         'Ender\'s Academy for wayward space boys')
        self.assertEqual(response['description'],
                         'A school, in outerspace, with weightless games')
        self.assertEqual(1, response['id'])
        self.assertIsNotNone(
            db.session.query(ThrivInstitution).filter_by(id=1).first())

    def test_list_institutions(self):
        i1 = ThrivInstitution(name="Delmar's", description="autobody")
        i2 = ThrivInstitution(
            name="News Leader", description="A once formidable news source")
        db.session.add(i1)
        db.session.add(i2)
        db.session.commit()
        rv = self.app.get('/api/institution', content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(2, len(response))

    def test_list_institutions_with_availability(self):
        i1 = ThrivInstitution(
            name="Delmar's", description="autobody", hide_availability=True)
        i2 = ThrivInstitution(
            name="News Leader",
            description="A once formidable news source",
            hide_availability=False)
        i3 = ThrivInstitution(
            name="Baja", description="Yum. Is it lunch time?")
        db.session.add_all([i1, i2, i3])
        db.session.commit()
        rv = self.app.get(
            '/api/institution/availability', content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(2, len(response))

    def test_delete_institution(self):
        institution = {
            "name": "Ender's Academy for wayward space boys",
            "description": "A school, in outerspace, with weightless games"
        }
        rv = self.app.post(
            '/api/institution',
            data=json.dumps(institution),
            content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        rv = self.app.delete('/api/institution/%i' % response['id'])
        self.assertSuccess(rv)
        self.assertEqual(
            0,
            db.session.query(ThrivInstitution).filter_by(id=1).count())

    def test_modify_institution(self):
        institution = {
            "name": "Ender's Academy for wayward space boys",
            "description": "A school, in outerspace, with weightless games"
        }
        rv = self.app.post(
            '/api/institution',
            data=json.dumps(institution),
            content_type="application/json")
        response = json.loads(rv.get_data(as_text=True))
        response["name"] = "My little bronnie"
        response["description"] = "A biopic on the best and brightest " \
                                  "adults who are 'My Little Pony' fans."
        rv = self.app.put(
            '/api/institution/%i' % response['id'],
            data=json.dumps(response),
            content_type="application/json")
        self.assertSuccess(rv)
        rv = self.app.get('/api/institution/%i' % response["id"])
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual("My little bronnie", response["name"])
