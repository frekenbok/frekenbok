from django.test import TestCase
from django.conf import settings

from django.db.utils import IntegrityError
from autofixture.generators import ChoicesGenerator

from autofixture import AutoFixture
from moneyed import Decimal, RUB, EUR, USD, SAR, JPY

from accountant.models import Account, Sheaf


class AccountTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.accounts = AutoFixture(Account).create(1)
        for account in cls.accounts:
            AutoFixture(
                Sheaf,
                field_values={
                    'account': account,
                    'currency': ChoicesGenerator(values=(RUB, EUR, USD))
                }
            ).create(3)

    def test_sorted_sheaves(self):
        currencies = [i.currency for i in self.accounts[0].sorted_sheaves]

        self.assertEqual(currencies[0], settings.BASE_CURRENCY)

        self.assertEqual(
            currencies[1:],
            sorted(currencies[1:])
        )


class SheafTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.accounts = AutoFixture(Account).create(1)
        for account in cls.accounts:
            AutoFixture(
                Sheaf,
                field_values={
                    'account': account,
                    'currency': ChoicesGenerator(values=(RUB, EUR, USD, SAR))
                }
            ).create(3)

    def test_one_sheaf_currency_for_per_account(self):
        Sheaf.objects.create(account=self.accounts[0],
                             amount=Decimal('34532.12'),
                             currency=JPY)

        with self.assertRaises(IntegrityError):
            Sheaf.objects.create(account=self.accounts[0],
                                 amount=Decimal('932.12'),
                                 currency=JPY)
