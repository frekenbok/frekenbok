from datetime import date

from django.test import TestCase
from django.conf import settings

from django.db.utils import IntegrityError

from moneyed import Decimal, JPY, USD

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


class TransactionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def test_save_new_transaction_new_sheaf(self):
        amount = Decimal('3252.34')
        currency = JPY

        sheaves = {i.currency: i.amount for i in self.wallet.sheaves.all()}
        self.assertNotIn(str(currency), sheaves)

        Transaction.objects.create(account=self.wallet,
                                   amount=amount,
                                   currency=currency,
                                   date=date.today(),
                                   invoice=self.first_salary)

        upd_sheaves = {i.currency: i.amount for i in self.wallet.sheaves.all()}
        self.assertIn(str(currency), upd_sheaves)
        self.assertEqual(upd_sheaves[str(currency)], amount)

    def test_save_new_transaction_old_sheaf(self):
        amount = Decimal('214.20')
        currency = USD

        sheaves = {i.currency: i.amount for i in self.wallet.sheaves.all()}
        self.assertIn(str(currency), sheaves)
        old_amount = sheaves[str(currency)]

        Transaction.objects.create(account=self.wallet,
                                   amount=amount,
                                   currency=currency,
                                   date=date.today(),
                                   invoice=self.first_salary)

        upd_sheaves = {i.currency: i.amount for i in self.wallet.sheaves.all()}
        self.assertIn(str(currency), upd_sheaves)
        self.assertEqual(upd_sheaves[str(currency)],
                         old_amount + amount)

    def test_save_old_transaction(self):
        amount = Decimal('0.05')
        currency = USD

        old_amount = Sheaf.objects.filter(account=self.wallet,
                                          currency=currency).first().amount

        transaction = self.first_bonus.transactions.get(account=self.wallet)
        transaction.amount -= amount
        transaction.save()

        upd_sheaves = {i.currency: i.amount for i in self.wallet.sheaves.all()}
        self.assertIn(str(currency), upd_sheaves)
        self.assertEqual(upd_sheaves[str(currency)],
                         old_amount - amount)


class InvoiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def test_verify_method_with_correct_invoice(self):
        self.assertEqual(self.first_salary.verify(),
                         dict())

    def test_verify_method_with_incorrect_invoice(self):
        self.first_salary.transactions.filter(amount__lt=0).first().delete()
        self.assertEqual(self.first_salary.verify(),
                         {'RUB': Decimal('70000')})

    def test_is_verified_property_with_correct_invoice(self):
        self.assertTrue(self.first_salary.is_verified)

    def test_is_verified_property_with_incorrect_invoice(self):
        self.first_salary.transactions.filter(amount__lt=0).first().delete()
        self.assertFalse(self.first_salary.is_verified)
