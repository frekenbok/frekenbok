from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.views.generic.base import ContextMixin

from .test_data import prepare_test_data

from accountant.models import Account
from accountant.views import AccountantViewMixin, DashboardView, AccountListView, IncomeListView


class AccountantViewMixinTestCase(TestCase):
    def setUp(self):
        self.mixin = AccountantViewMixin()

    def tearDown(self):
        del self.mixin

    def test_is_instance_of_context_mixin(self):
        self.assertIsInstance(self.mixin, ContextMixin)

    def test_context_contains_accountant_app(self):
        context = self.mixin.get_context_data()
        self.assertTrue(context.get('accountant_app'))


class DashboardViewTestCase(TestCase):
    def setUp(self):
        prepare_test_data(self)
        self.client = Client()
        self.view = DashboardView()

    def tearDown(self):
        del self.view
        del self.client

    def test_get_queryset(self):
        for item in self.view.get_queryset():
            self.assertEqual(item.type, Account.ACCOUNT)

    def test_is_subcalss_of_accountant_view_mixin(self):
        self.assertIsInstance(self.view, AccountantViewMixin)

    def test_type_of_accounts_in_queryset(self):
        queryset = self.view.get_queryset()
        for account in queryset:
            self.assertEqual(account.type, Account.ACCOUNT)

    def test_context_for_menu_dashboard(self):
        context = self.client.get(reverse('accountant:dashboard')).context
        self.assertTrue(context['menu_dashboard'])


class AccountListViewTestCase(TestCase):
    def setUp(self):
        prepare_test_data(self)
        self.view = AccountListView()

    def tearDown(self):
        del self.view

    def test_is_subcalss_of_accountant_view_mixin(self):
        self.assertIsInstance(self.view, AccountantViewMixin)

    def test_type_of_accounts_in_queryset(self):
        queryset = self.view.get_queryset()
        for account in queryset:
            self.assertEqual(account.type, Account.ACCOUNT)


class IncomeListViewTestCase(TestCase):
    def setUp(self):
        prepare_test_data(self)
        self.view = IncomeListView()

    def tearDown(self):
        del self.view

    def test_is_subcalss_of_accountant_view_mixin(self):
        self.assertIsInstance(self.view, AccountantViewMixin)

    def test_type_of_accounts_in_queryset(self):
        queryset = self.view.get_queryset()
        for account in queryset:
            self.assertEqual(account.type, Account.INCOME)
