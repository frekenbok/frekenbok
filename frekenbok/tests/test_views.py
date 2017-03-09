from datetime import date

from django.conf import settings
from django.test import TestCase, Client
from django.urls import reverse

from accountant.models import Account
from frekenbok.tests.test_data import add_test_data
from frekenbok.views import DashboardView


class DashboardViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.test_user.username,
                          password=self.test_user_password)
        response = self.client.get(reverse('dashboard'))
        self.context = response.context
        self.view = DashboardView()

    def tearDown(self):
        del self.view
        del self.client
        del self.context

    def test_type_of_accounts_in_queryset(self):
        for account in self.view.get_queryset():
            self.assertEqual(account.type, Account.ACCOUNT)

    def test_context_menu_dashboard(self):
        self.assertTrue(self.context['menu_dashboard'])

    def test_context_account_list(self):
        for account in self.context['account_list']:
            self.assertIsInstance(account, Account)

        accounts = Account.objects.filter(type=Account.ACCOUNT)
        expected_accounts = [i for i in accounts
                             if i.get_children_count() == 0 and
                             (not i.closed or i.closed >= date.today())]

        self.assertEqual(len(expected_accounts),
                         len(self.context['account_list']))

    def test_context_account_list_after_account_remove(self):
        self.reserve.delete()
        context = self.client.get(reverse('dashboard')).context

        accounts = Account.objects.filter(type=Account.ACCOUNT)
        children_less = [i for i in accounts if i.get_children_count() == 0]

        self.assertEqual(len(children_less), len(context['account_list']))

    def test_context_total(self):
        total = self.context['total']
        self.assertEqual(total[0]['currency'], settings.BASE_CURRENCY)
        self.assertEqual(
            [i['currency'] for i in total[1:]],
            sorted(i['currency'] for i in total[1:])
        )

    def test_contex_overview(self):
        expected_overview = Account.objects.filter(type=Account.ACCOUNT,
                                                   depth=1)
        overview = self.context['overview']

        self.assertEqual(len(expected_overview), len(overview))
        for account in overview:
            self.assertEqual(account['weight'],
                             sum(i['amount'] for i in account['report']))

    def test_login_less_request(self):
        client = Client()
        response = client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 403)
