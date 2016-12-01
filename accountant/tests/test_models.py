from django.test import TestCase
from django.conf import settings

from django.db.utils import IntegrityError

from moneyed import Decimal, JPY

from accountant.models import Sheaf

from .test_data import add_test_data


class AccountTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def test_sorted_sheaves(self):
        currencies = [i.currency for i in self.wallet.sorted_sheaves]

        self.assertEqual(currencies[0], settings.BASE_CURRENCY)

        self.assertEqual(
            currencies[1:],
            sorted(currencies[1:])
        )


class SheafTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def test_one_sheaf_currency_for_per_account(self):
        Sheaf.objects.create(account=self.wallet,
                             amount=Decimal('34532.12'),
                             currency=JPY)

        with self.assertRaises(IntegrityError):
            Sheaf.objects.create(account=self.wallet,
                                 amount=Decimal('932.12'),
                                 currency=JPY)
