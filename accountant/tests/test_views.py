import json
from datetime import date, datetime

from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.views.generic.base import ContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings

from accountant.models import Account
from accountant.views import AccountantViewMixin, DashboardView, AccountDetailView, AccountListView, IncomeListView

from .test_data import add_test_data


class AccountantViewMixinTestCase(TestCase):
    def setUp(self):
        self.mixin = AccountantViewMixin()

    def tearDown(self):
        del self.mixin

    def test_is_instance_of_context_mixin(self):
        self.assertIsInstance(self.mixin, ContextMixin)

    def test_is_instance_of_login_required_mixin(self):
        self.assertIsInstance(self.mixin, LoginRequiredMixin)

    def test_context_contains_accountant_app(self):
        context = self.mixin.get_context_data()
        self.assertTrue(context.get('accountant_app'))


class DashboardViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.test_user.username,
                          password=self.test_user_password)
        response = self.client.get(reverse('accountant:dashboard'))
        self.context = response.context
        self.view = DashboardView()

    def tearDown(self):
        del self.view
        del self.client
        del self.context

    def test_is_instance_of_accountant_view_mixin(self):
        self.assertIsInstance(self.view, AccountantViewMixin)

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
        context = self.client.get(reverse('accountant:dashboard')).context

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
        response = client.get(reverse('accountant:dashboard'))
        self.assertEqual(response.status_code, 403)


class AccountDetailViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def setUp(self):
        self.client = Client()
        self.context = self.client.get(reverse('accountant:account_detail',
                                               kwargs={'pk': 3})).context
        self.view = AccountDetailView()

    def tearDown(self):
        del self.view
        del self.client
        del self.context

    def test_is_instance_of_accountant_view_mixin(self):
        self.assertIsInstance(self.view, AccountantViewMixin)

    def test_login_less_request(self):
        client = Client()
        response = client.get(reverse('accountant:account_detail',
                                      kwargs={'pk': 3}))
        self.assertEqual(response.status_code, 403)


class AccountListViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def setUp(self):
        self.view = AccountListView()
        self.query_set = self.view.get_queryset()

    def tearDown(self):
        del self.view

    def test_is_instance_of_accountant_view_mixin(self):
        self.assertIsInstance(self.view, AccountantViewMixin)

    def test_type_of_accounts_in_queryset(self):
        for account in self.query_set:
            self.assertEqual(account.type, Account.ACCOUNT)

    def test_closed_date_in_queryset(self):
        for account in self.query_set:
            self.assertTrue(
                not account.closed or account.closed >= date.today()
            )

    def test_login_less_request(self):
        client = Client()
        response = client.get(reverse('accountant:account_list'))
        self.assertEqual(response.status_code, 403)


class IncomeListViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def setUp(self):
        self.view = IncomeListView()
        self.query_set = self.view.get_queryset()

    def tearDown(self):
        del self.view

    def test_is_instance_of_accountant_view_mixin(self):
        self.assertIsInstance(self.view, AccountantViewMixin)

    def test_type_of_accounts_in_queryset(self):
        for account in self.query_set:
            self.assertEqual(account.type, Account.INCOME)

    def test_closed_date_in_queryset(self):
        for account in self.query_set:
            self.assertTrue(
                not account.closed or account.closed >= date.today()
            )

    def test_login_less_request(self):
        client = Client()
        response = client.get(reverse('accountant:income_list'))
        self.assertEqual(response.status_code, 403)


class SmsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def setUp(self):
        self.client = Client()
        self.payload = {
            'secret': settings.SMS_SECRET_KEY,
            'from': 'Tinkoff',
            'message_id': 2871592331456,
            'message': 'Some message text',
            'sent_timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'sent_to': '+79111234567',
            'device_id': 'my_device'
        }

    def tearDown(self):
        del self.client
        del self.payload

    def test_with_unknown_sender(self):
        self.payload['from'] = 'Captain Kirk'
        response = self.client.post(
            path=reverse('accountant:sms'),
            data=json.dumps(self.payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 404)

    def test_with_wrong_secret_key(self):
        self.payload['secret'] = 'some_very_secret_but_wrong_key'
        response = self.client.post(
            path=reverse('accountant:sms'),
            data=json.dumps(self.payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)

