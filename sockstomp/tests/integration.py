
from sockstomp.tests import IntegrationTestBase
from pyramid.httpexceptions import HTTPUnauthorized

from webtest import AppError

class IntegrationTestViews(IntegrationTestBase):
    def test_static_files(self):
        res = self.app.get('/static/index.html')
        self.assertEqual(res.status_int, 200)

    def test_login_succeeds(self):
        """ Call the login view, make sure routes are working """
        credentials = {
            'username': 'admin',
            'password': 'admin',
            }

        res = self.app.post_json('/account/login/', credentials)
        
        self.assertEqual(res.status_int, 200)
        self.assertTrue('jwt' in res.json_body)

    def test_login_fail(self):
        """ Call the login view, make sure routes are working """
        credentials = {
            'username': 'unknown',
            'password': 'unknown',
            }

        res = self.app.post_json('/account/login/', credentials, expect_errors=True)
        self.assertEqual(res.status_int, 401)
          