import json
import logging

from django.test import SimpleTestCase

from SocialAdda.logs import JsonFormatter


class JsonLogTests(SimpleTestCase):
    def test_each_record_is_one_json_object(self):
        record = logging.LogRecord('app', logging.WARNING, __file__, 1, 'disk %s', ('almost full',), None)
        line = JsonFormatter().format(record)
        payload = json.loads(line)
        self.assertEqual(payload['level'], 'WARNING')
        self.assertEqual(payload['message'], 'disk almost full')
        self.assertNotIn('\n', line)
