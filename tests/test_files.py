import datetime
import json
from io import BytesIO

import requests

from tests.base_test import BaseTest
from app.models import UploadedFile
from app.resources.schema import FileSchema


class TestFiles(BaseTest):

    def test_add_file(self):
        file = UploadedFile(
            file_name='happy_coconuts.svg',
            display_name='Happy Coconuts',
            date_modified=datetime.datetime.now(),
            md5="3399")
        rv = self.app.post(
            '/api/file',
            data=json.dumps(FileSchema().dump(file).data),
            content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        file_id = response["id"]
        raw_data = BytesIO(b"<svg xmlns=\"http://www.w3.org/2000/svg\"/>")
        rv = self.app.put(
            '/api/file/%i' % file_id, data=raw_data, content_type='image/svg')
        self.assertSuccess(rv)
        data = json.loads(rv.get_data(as_text=True))
        self.assertEqual(
            "https://s3.amazonaws.com/edplatform-ithriv-test-bucket/"
            "ithriv/resource/attachment/%i.svg" % file_id, data["url"])
        self.assertEqual('happy_coconuts.svg', data['file_name'])
        self.assertEqual('Happy Coconuts', data['display_name'])
        self.assertIsNotNone(data['date_modified'])
        self.assertEqual('image/svg', data['mime_type'])
        self.assertEqual("3399", data['md5'])
        return data

    def test_remove_file(self):
        file_data = self.test_add_file()
        response = requests.get(file_data['url'])
        self.assertEqual(200, response.status_code)
        rv = self.app.delete('/api/file/%i' % file_data['id'])
        self.assertSuccess(rv)
        response = requests.get(file_data['url'])
        self.assertEqual(404, response.status_code)

    def test_attach_file_to_resource(self):
        r = self.construct_resource()
        file = self.test_add_file()
        file['resource_id'] = r.id
        rv = self.app.put(
            '/api/file/%i' % file['id'],
            data=json.dumps(file),
            content_type="application/json")
        self.assertSuccess(rv)
        rv = self.app.get(
            '/api/resource/%i' % r.id, content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(1, len(response['files']))
        self.assertEqual("happy_coconuts.svg",
                         response['files'][0]['file_name'])


    def test_find_attachment_by_md5(self):
        f1 = self.addFile()
        f2 = self.addFile(md5='123412341234')
        f3 = self.addFile(md5='666666666666', display_name="Lots a 6s")
        rv = self.app.get(
            '/api/file?md5=666666666666', content_type="application/json")
        self.assertSuccess(rv)
        response = json.loads(rv.get_data(as_text=True))
        self.assertEqual(1, len(response))
        self.assertEqual("Lots a 6s", response[0]['display_name'])
