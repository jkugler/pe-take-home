import json
from pathlib import Path
import os
import unittest

from werkzeug.exceptions import NotFound

import main

class TestIncedentDAO(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        data_file = os.path.join(Path(__file__).parent.parent, 'data', 'F01705150050.json')
        data_file2 = os.path.join(Path(__file__).parent.parent, 'data', 'F01705150090.json')
        self.data = json.loads(open(data_file).read())
        self.data2 = json.loads(open(data_file2).read())

        unittest.TestCase.__init__(self, *args, **kwargs)

    def setUp(self):
        self.dao = main.IncidentDAO()

    def tearDown(self):
        os.unlink('db/incident.db')

    def test_extract_data(self):
        extracted_data = self.dao._extract_data(self.data)
        self.assertEqual(extracted_data[0], 'F01705150050')
        self.assertEqual(extracted_data[6], '2017-05-15T13:19:12-04:00')

    def test_invalid_data_structure(self):
        my_data = dict(self.data)
        del(my_data['description']['incident_number'])
        self.assertRaises(ValueError, self.dao._extract_data, my_data)

    def test_create_and_get(self):
        # create() returns the record via .get()
        create_result = self.dao.create(self.data)
        self.assertEqual(create_result['id'], 'F01705150050')

    def test_delete(self):
        self.dao.create(self.data)
        self.dao.delete('F01705150050')
        self.assertRaises(NotFound, self.dao.get, 'F01705150050')

    def test_list_all(self):
        self.dao.create(self.data)
        self.dao.create(self.data2)
        result = self.dao.incedents()
        self.assertEqual(result[0]['id'], 'F01705150050')
        self.assertEqual(result[1]['id'], 'F01705150090')

    def test_update(self):
        self.dao.create(self.data)
        my_data = dict(self.data)
        my_data['address']['address_line1'] = '333 E FRANKLIN RD'
        self.dao.update('F01705150050', my_data)
        result = self.dao.get('F01705150050')
        self.assertEqual(result['address'], '333 E FRANKLIN RD')

    def test_update_with_invalid_inc_id(self):
        self.dao.create(self.data)
        my_data = dict(self.data)
        my_data['description']['incident_number'] = 'INVALID'
        self.assertRaises(ValueError, self.dao.update, 'F01705150050', my_data)

    def test_create_already_existing(self):
        self.dao.create(self.data)
        self.assertRaises(RuntimeError, self.dao.create, self.data)

class TestWebApp(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        data_file = os.path.join(Path(__file__).parent.parent, 'data', 'F01705150050.json')
        data_file2 = os.path.join(Path(__file__).parent.parent, 'data', 'F01705150090.json')
        self.data = open(data_file).read()
        self.data2 = open(data_file2).read()
        self.app = main.app

        unittest.TestCase.__init__(self, *args, **kwargs)

    def tearDown(self):
        os.unlink('db/incident.db')

    def test_inc_create_and_get(self):
        with self.app.test_client() as c:
            resp = c.post('/api/', json=json.loads(self.data))
            resp_data = json.loads(resp.data)
            self.assertEqual(resp_data['id'], 'F01705150050')

    def test_create_already_existing(self):
        with self.app.test_client() as c:
            c.post('/api/', json=json.loads(self.data))
            resp = c.post('/api/', json=json.loads(self.data))
            self.assertEqual(resp.status, '400 BAD REQUEST')

    def test_get_all_incs(self):
        with self.app.test_client() as c:
            c.post('/api/', json=json.loads(self.data))
            c.post('/api/', json=json.loads(self.data2))
            resp = c.get('/api/')
            resp_data = json.loads(resp.data)
            self.assertEqual(resp_data[0]['id'], 'F01705150050')
            self.assertEqual(resp_data[1]['id'], 'F01705150090')

    def test_get_inc(self):
        with self.app.test_client() as c:
            c.post('/api/', json=json.loads(self.data))
            resp = c.get('/api/F01705150050')
            resp_data = json.loads(resp.data)
            self.assertEqual(resp_data['id'], 'F01705150050')

    def test_delete(self):
        with self.app.test_client() as c:
            c.post('/api/', json=json.loads(self.data))
            c.delete('/api/F01705150050')
            resp = c.get('/api/F01705150050')
            self.assertEqual(resp.status, '404 NOT FOUND')

    def test_delete_invalid(self):
        with self.app.test_client() as c:
            resp = c.delete('/api/INVALID')
            self.assertEqual(resp.status, '404 NOT FOUND')

    def test_update(self):
        with self.app.test_client() as c:
            c.post('/api/', json=json.loads(self.data))
            my_data = json.loads(self.data)
            my_data['address']['address_line1'] = '333 E FRANKLIN RD'
            c.put('/api/F01705150050', json=my_data)
            resp = c.get('/api/F01705150050')
            resp_data = json.loads(resp.data)
            self.assertEqual(resp_data['address'], '333 E FRANKLIN RD')

    def test_update_invalid(self):
        with self.app.test_client() as c:
            resp = c.put('/api/INVALID', json=json.loads(self.data))
            self.assertEqual(resp.status, '404 NOT FOUND')


    def test_update_not_matching_id(self):
        with self.app.test_client() as c:
            c.post('/api/', json=json.loads(self.data))
            c.post('/api/', json=json.loads(self.data2))
            resp = c.put('/api/F01705150090', json=json.loads(self.data))
            self.assertEqual(resp.status, '400 BAD REQUEST')
