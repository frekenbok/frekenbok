from django.test import TestCase
from django.conf import settings

from django.db.utils import IntegrityError

from moneyed import Decimal, JPY

from accountant.models import Sheaf, Transaction

from .test_data import add_test_data


class AccountTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def test_recalculate_account_summary(self):
        self.wallet.recalculate_summary()

        transactions = Transaction.objects.filter(account=self.wallet).all()
        expected_sheaves = dict()
        for transaction in transactions:
            expected_sheaves.setdefault(transaction.currency, Decimal(0))
            expected_sheaves[transaction.currency] += transaction.amount
        actual_sheaves = {i.currency: i.amount
                          for i in self.wallet.sheaves.all()}

        self.assertEqual(len(expected_sheaves), len(actual_sheaves))
        for key in actual_sheaves:
            self.assertEqual(expected_sheaves[key],
                             actual_sheaves[key])

    def test_recalculate_account_summary_drops_odd_sheaves(self):
        Sheaf.objects.create(account=self.wallet,
                             currency=JPY,
                             amount=Decimal(234)).save()
        self.wallet.recalculate_summary()

        actual_sheaves = {i.currency: i.amount
                          for i in self.wallet.sheaves.all()}
        self.assertNotIn('JPY', actual_sheaves)

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
