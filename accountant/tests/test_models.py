from django.test import TestCase
from django.conf import settings

from django.db.utils import IntegrityError
from autofixture.base import CreateInstanceError

from autofixture import AutoFixture
from moneyed import Decimal, SAR

from accountant.models import Account, Sheaf


class AccountTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.accounts = AutoFixture(Account).create(1)
        for account in cls.accounts:
            for i in range(3):
                try:
                    AutoFixture(
                        Sheaf,
                        field_values={'account': account}
                    ).create_one()
                except CreateInstanceError:
                    continue

    def test_sorted_sheaves(self):
        currencies = [i.currency for i in self.accounts[0].sheaves.all()]

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
            for i in range(3):
                try:
                    AutoFixture(
                        Sheaf,
                        field_values={'account': account}
                    ).create_one()
                except CreateInstanceError:
                    continue

    def test_one_sheaf_currency_for_per_account(self):
        Sheaf.objects.create(account=self.accounts[0],
                             amount=Decimal('34532.12'),
                             currency=SAR)

        with self.assertRaises(IntegrityError):
            Sheaf.objects.create(account=self.accounts[0],
                                 amount=Decimal('932.12'),
                                 currency=SAR)
