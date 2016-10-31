from django.test import TestCase

from .test_data import prepare_test_data

from accountant.models import Account
from accountant.views import DashboardView

class DashboardViewTestCase(TestCase):
    def setUp(self):
        prepare_test_data(self)
        self.view = DashboardView()

    def test_get_queryset(self):
        for item in self.view.get_queryset():
            self.assertEqual(item.type, Account.ACCOUNT)

    def test_get_context_data_mixin_included(self):
        context = self.view.get_context_data()
        self.assertTrue(context['accountant_app'])
