
from sockstomp.tests import UnitTestBase

# skip below unit test case example
# ---------------------------------
# class UnitTestViews(UnitTestBase):
#     def test_login_succeeds(self):
#         """ Make sure we can login """
#         admin = User(username='sontek', password='temp', kind=u'admin')
#         admin.activated = True
#         self.session.add(admin)
#         self.session.flush()

#         from app.accounts.views import LoginView
#         self.config.add_route('index', '/')
#         self.config.add_route('dashboard', '/dashboard')

#         request = self.get_csrf_request(post={
#             'submit': True,
#             'Username': 'sontek',
#             'Password': 'temp',
#             })

#         view = LoginView(request)
#         response = view.post()

#         self.assertEqual(response.status_int, 302)
