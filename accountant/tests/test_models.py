import logging
from datetime import date, timedelta

from django.conf import settings
from django.db.utils import IntegrityError
from django.test import TestCase
from moneyed import Decimal, JPY, USD, ZAR
from typing import Iterable

from accountant.models import Sheaf, Transaction, Account
from frekenbok.tests.test_data import add_test_data

logger = logging.getLogger(__name__)


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

    def test_recalculate_account_summary_ignores_not_approved_transactions(self):
        self.wallet.recalculate_summary()
        old_summary = self.wallet.sorted_sheaves
        future_transaction = Transaction.objects.create(
            date=date.today(), amount=200, currency=ZAR, account=self.wallet,
            approved=False
        )
        self.wallet.recalculate_summary()

        new_summary = self.wallet.sorted_sheaves
        self.assertEqual(old_summary, new_summary)

    def test_summary_at(self):
        self.wallet.recalculate_summary()
        expected_summary = [{'amount': i.amount, 'currency': i.currency}
                            for i in self.wallet.sheaves.all()]
        near_future_date = date.today() + timedelta(days=10)
        report_date = date.today() + timedelta(days=15)
        far_future_date = date.today() + timedelta(days=20)

        near_transaction = Transaction.objects.create(
            date=near_future_date,
            amount=Decimal('500'),
            currency=ZAR,
            account=self.wallet
        )
        far_transaction = Transaction.objects.create(
            date=far_future_date,
            amount=Decimal('500'),
            currency=ZAR,
            account=self.wallet
        )

        expected_summary.append({'amount': Decimal('500'), 'currency': 'ZAR'})
        future_summary = self.wallet.summary_at(report_date)

        logger.debug('Expected summary: {}'.format(expected_summary))
        logger.debug('Future summary: {}'.format(future_summary))

        self.assertEqual(len(expected_summary), len(future_summary))
        for future, current in zip(future_summary, expected_summary):
            self.assertEqual(future['amount'], current['amount'])
            self.assertEqual(future['currency'], current['currency'])

    def test_sorted_sheaves(self):
        currencies = [i.currency for i in self.wallet.sorted_sheaves]

        self.assertEqual(currencies[0], settings.BASE_CURRENCY)

        self.assertEqual(
            currencies[1:],
            sorted(currencies[1:])
        )

    def test_tree_summary(self):
        expected_tree_summary = dict()
        for account in self.cash.get_children():
            for sheaf in account.sheaves.all():
                expected_tree_summary.setdefault(sheaf.currency, Decimal(0))
                expected_tree_summary[sheaf.currency] += sheaf.amount
        expected_result = [{'currency': key, 'amount': value}
                           for key, value in expected_tree_summary.items()]
        expected_result.sort(key=lambda x: x['currency'])

        self.assertEqual(expected_result, list(self.cash.tree_summary()))

    @staticmethod
    def sorted_ids(accounts: Iterable[Account]):
        sorted([i.id for i in accounts])

    def test_get_expenses(self):
        self.assertEqual(
            self.sorted_ids(Account.get_expenses()),
            self.sorted_ids(self.expenses)
        )

    def test_get_accounts(self):
        self.assertEqual(
            self.sorted_ids(Account.get_accounts()),
            self.sorted_ids(self.accounts)
        )

    def test_get_incomes(self):
        self.assertEqual(
            self.sorted_ids(Account.get_incomes()),
            self.sorted_ids(self.incomes)
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

    def test_eq(self):
        self.wallet.recalculate_summary()
        some_sheaf = self.wallet.sorted_sheaves[0]
        # Recalculate summary should drop old sheaves
        self.wallet.recalculate_summary()
        other_sheaf = self.wallet.sorted_sheaves[0]

        self.assertEqual(some_sheaf, other_sheaf)

    def test_ne(self):
        self.wallet.recalculate_summary()
        some_sheaf = self.wallet.sorted_sheaves[0]

        Transaction.objects.create(
            date=date.today(),
            account=self.wallet,
            amount=Decimal('234'),
            currency=some_sheaf.currency
        )
        other_sheaf = self.wallet.sorted_sheaves[0]

        self.assertNotEqual(some_sheaf, other_sheaf)


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

    def test_save_old_transaction_old_account(self):
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

    def test_save_old_transaction_new_account(self):
        transaction = self.first_bonus.transactions.get(account=self.wallet)
        old_sheaves = {i.currency: i.amount for i in self.wallet.sheaves.all()}

        transaction.account = self.reserve
        transaction.save()
        new_sheaves = {i.currency: i.amount for i in self.wallet.sheaves.all()}

        self.assertEqual(
            new_sheaves.get(transaction.currency, Decimal('0')),
            old_sheaves[transaction.currency] - transaction.amount
        )


class InvoiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def test_verify_method_with_correct_invoice(self):
        result = self.first_salary.verify()

        logger.debug('Verification result: {}'.format(result))
        self.assertEqual(list(result), list())

    def test_verify_method_with_incorrect_invoice(self):
        transaction_to_delete = self.first_salary.transactions.first()
        expected_result = [{'currency': transaction_to_delete.currency,
                            'amount': -transaction_to_delete.amount}]
        transaction_to_delete.delete()

        self.assertEqual(list(self.first_salary.verify()), expected_result)

    def test_is_verified_property_with_correct_invoice(self):
        self.assertTrue(self.first_salary.is_verified)

    def test_is_verified_property_with_incorrect_invoice(self):
        self.first_salary.transactions.filter(amount__lt=0).first().delete()
        self.assertFalse(self.first_salary.is_verified)

    def test_pnl_property(self):
        expected_result = dict()
        for transaction in self.first_salary.transactions.all():
            if transaction.account.type == Account.ACCOUNT:
                expected_result.setdefault(transaction.currency, Decimal(0))
                expected_result[transaction.currency] += transaction.amount
        expected_result = [
            {
                'currency': i[0],
                'amount': i[1]
            }
            for i in sorted(list(expected_result.items()), key=lambda x: x[0])
        ]

        self.assertEqual(list(self.first_salary.pnl), expected_result)

    def test_incomes_property(self):
        self.assertEqual(list(self.first_salary.incomes), [self.salary])

    def test_expenses_property(self):
        self.assertEqual(set(self.first_invoice.expenses), set(self.expenses))

    def test_accounts_property(self):
        self.assertEqual(list(self.first_salary.accounts), [self.wallet])

    def test_income_transactions_property(self):
        self.assertEqual(
            list(self.first_salary.income_transactions)[0],
            self.first_salary_income_tx
        )

    def test_internal_transactions_property(self):
        self.assertEqual(
            list(self.first_salary.internal_transactions)[0],
            self.first_salary_internal_tx
        )

    def test_expense_transactions_property(self):
        self.assertEqual(
            list(self.third_invoice.expense_transactions)[0],
            self.third_invoice_expense_tx
        )


class DocumentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        add_test_data(cls)

    def test_mime_type_property(self):
        self.assertEqual(self.document_as_pdf.mime_type, 'application/pdf')
        self.assertEqual(self.document_as_img.mime_type, 'image/jpeg')

    def test_json_method(self):
        expected_result = {
            'description': self.document_as_pdf.description,
            'id': self.document_as_pdf.id,
            'invoice': self.invoice_with_attached_image.id
        }
        expected_path = '/media/documents/{}/{}/test_doc'.format(
            date.today().year, date.today().month
        )

        actual_result = self.document_as_pdf.json()
        url = actual_result.pop('file')

        self.assertEqual(expected_result, actual_result)
        self.assertTrue(url.startswith(expected_path))

    def test_json_method_for_invoiceless_document(self):
        self.assertIsNone(self.document_without_invoice.json()['invoice'])
