from .base import ApiTestCase


class SchemaTests(ApiTestCase):
    def test_openapi_schema_is_served_and_lists_endpoints(self):
        response = self.api.get('/api/schema/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/api/v1/posts/', response.content)

    def test_swagger_ui_is_served(self):
        self.assertEqual(self.api.get('/api/docs/').status_code, 200)
