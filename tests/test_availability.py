import json

from tests.base_test import BaseTest
from app import db
from app.models import Availability


class TestAvailability(BaseTest):
    def test_add_availability(self):
        r = self.construct_resource()
        institution = self.construct_institution(
            name="Delmar's", description="autobody")

        availability_data = {
            "resource_id": r.id,
            "institution_id": institution.id,
            "available": True
        }

        rv = self.app.post(
            '/api/availability',
            data=json.dumps(availability_data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(institution.id, response["institution_id"])
        self.assertEqual(r.id, response["resource_id"])
        self.assertEqual(True, response["available"])

    def test_add_availability_via_resource(self):
        r = self.construct_resource()
        institution = self.construct_institution(
            name="Delmar's", description="autobody")

        availability_data = [{
            "resource_id": r.id,
            "institution_id": institution.id,
            "available": True
        }]

        rv = self.app.post(
            '/api/resource/%i/availability' % r.id,
            data=json.dumps(availability_data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(institution.id, response[0]["institution_id"])
        self.assertEqual(r.id, response[0]["resource_id"])
        self.assertEqual(True, response[0]["available"])

    def test_remove_availability(self):
        self.test_add_availability()
        rv = self.app.get(
            '/api/availability/%i' % 1, content_type="application/json")
        self.assertSuccess(rv)
        rv = self.app.delete('/api/availability/%i' % 1)
        self.assertSuccess(rv)
        rv = self.app.get(
            '/api/availability/%i' % 1, content_type="application/json")
        self.assertEqual(404, rv.status_code)

    def test_set_all_availability(self):
        r = self.construct_resource()
        i1 = self.construct_institution(
            name="Delmar's", description="autobody")
        i2 = self.construct_institution(
            name="Frank's", description="printers n stuff")
        i3 = self.construct_institution(
            name="Rick's", description="custom cabinets")

        availability_data = [{
            "institution_id": i1.id,
            "resource_id": r.id,
            "available": True
        }, {
            "institution_id": i2.id,
            "resource_id": r.id,
            "available": True
        }, {
            "institution_id": i3.id,
            "resource_id": r.id,
            "available": True
        }]

        rv = self.app.post(
            '/api/resource/%i/availability' % r.id,
            data=json.dumps(availability_data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(3, len(response))

        availability_data = [{
            "institution_id": i2.id,
            "resource_id": r.id,
            "available": True
        }]

        rv = self.app.post(
            '/api/resource/%i/availability' % r.id,
            data=json.dumps(availability_data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))

        self.assertEqual(1, len(response))
        self.assertEqual(i2.id, response[0]["institution_id"])

        av = db.session.query(Availability).first()
        self.assertIsNotNone(av)

        av_id = av.id

        rv = self.app.get(
            '/api/availability/%i' % av_id, content_type="application/json")
        self.assertSuccess(rv)
        rv = self.app.delete('/api/availability/%i' % av_id)
        self.assertSuccess(rv)
        rv = self.app.get(
            '/api/availability/%i' % av_id, content_type="application/json")
        self.assertEqual(404, rv.status_code)
