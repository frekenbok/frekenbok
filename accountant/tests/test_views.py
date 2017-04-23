import json
import logging
from datetime import date, datetime
from decimal import Decimal

import pytz
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.test import TestCase, Client
from django.views.generic.base import ContextMixin

from accountant.models import Account, Transaction, Invoice
from accountant.views import AccountantViewMixin, \
    AccountDetailView, AccountListView, IncomeListView
from frekenbok.tests.test_data import add_test_data

logger = logging.getLogger(__name__)


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
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            '{}?next={}'.format(
                reverse('login'),
                reverse('accountant:account_detail', kwargs={'pk': 3})
            )
        )


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
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            '{}?next={}'.format(
                reverse('login'),
                reverse('accountant:account_list')
            )
        )


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
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            '{}?next={}'.format(
                reverse('login'),
                reverse('accountant:income_list')
            )
        )

class SmsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def __get_message(self):
        return ('Pokupka. {account}. Summa {amount} {currency}. '
                '{receiver}. {datetime}. '
                'Dostupno {amount} {currency}. Tinkoff.ru'.format(
                    account=self.account,
                    amount=self.amount,
                    currency=self.currency,
                    receiver=self.receiver,
                    datetime=self.datetime.strftime('%d.%m.%Y %H:%M'))
                )

    def __get_response(self):
        return self.client.get(
            path=reverse('accountant:sms'),
            data=self.payload,
        )

    def setUp(self):
        self.client = Client()
        self.account = self.card.bank_title
        self.amount = Decimal('145.40')
        self.currency = 'RUB'
        self.receiver = 'PYATEROCHKA 8120, MOSCOW'
        self.timezone = pytz.timezone('Europe/Moscow')
        self.datetime=datetime.now(tz=self.timezone).replace(second=0, microsecond=0)
        self.payload = {
            'secret': settings.SMS_SECRET_KEY,
            'phone': 'Tinkoff',
            'text': self.__get_message(),
            'sms_center': 'some_sms_center'
        }

    def tearDown(self):
        del self.client
        del self.account
        del self.amount
        del self.currency
        del self.receiver
        del self.timezone
        del self.datetime
        del self.payload

    def test_with_unknown_sender(self):
        self.payload['phone'] = 'Captain Kirk'

        self.assertEqual(self.__get_response().status_code, 404)

    def test_with_unknown_account(self):
        self.account = 'Secret account'
        self.payload['text'] = self.__get_message()

        self.assertEqual(self.__get_response().status_code, 404)

    def test_with_wrong_secret_key(self):
        self.payload['secret'] = 'some_very_secret_but_wrong_key'

        self.assertEqual(self.__get_response().status_code, 401)

    def test_with_correct_data(self):
        response = self.__get_response()
        logger.debug('Response body: {}'.format(response.content))

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)

        response_json = json.loads(response.content.decode())
        logger.debug('Response JSON: {}'.format(response_json))
        created_invoice = Invoice.objects.get(pk=response_json['invoice'])
        logger.debug('Created invoice: {}'.format(created_invoice))
        created_transaction = Transaction.objects.get(pk=response_json['transaction'])
        logger.debug('Created transaction: {}'.format(created_transaction))

        self.assertEqual(created_invoice.timestamp, self.datetime)
        self.assertEqual(created_invoice.comment, self.payload['text'])

        # Minus is required because 'Pokupka' is listed in negative_actions set
        self.assertEqual(created_transaction.amount, -self.amount)
        self.assertEqual(created_transaction.currency, self.currency)
        self.assertEqual(created_transaction.date, self.datetime.date())
        self.assertEqual(created_transaction.account, self.card)
        self.assertEqual(created_transaction.invoice, created_invoice)
        self.assertEqual(created_transaction.comment, self.receiver)
