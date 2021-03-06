import json
from datetime import date, datetime
from decimal import Decimal
from os.path import abspath, dirname, join
from unittest import TestCase
from testfixtures import LogCapture

from pytz import timezone
from django.contrib.auth.models import User
from moneyed import RUB

from accountant.misc.fns_parser import parse, is_valid_invoice
from accountant.models import Account, Transaction


class FnsInvoiceParserTestCase(TestCase):
    invoice_path = join(dirname(abspath(__file__)), 'test_fns_invoice.json')

    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            username='james_t_kirk',
            email='captain@enterprise.com',
            password='tiberius'
        )
        cls.account = Account(title='Wallet', type=Account.ACCOUNT)
        Account.add_root(instance=cls.account)
        cls.expense = Account(title='Other', type=Account.EXPENSE)
        Account.add_root(instance=cls.expense)
        cls.beer = Account(title='Beer', type=Account.EXPENSE)
        Account.add_root(instance=cls.beer)
        cls.wrong_beer = Account(title='Wrong beer', type=Account.ACCOUNT)
        Account.add_root(instance=cls.wrong_beer)

        cls.beer_comment = 'ПИВО ТРИ МЕДВЕДЯ СВЕТЛОЕ АЛК.4'
        cls.wrong_beer_comment = 'ПИВО ЧЕРНИГОВСКОЕ СВЕТЛОЕ АЛК.'
        # This transaction should be used to guess account and unit for transaction
        Transaction.objects.create(
            date=date.today(),
            account=cls.beer,
            amount=Decimal('124.56'),
            currency=RUB,
            quantity=5,
            unit='l',
            comment=cls.beer_comment
        )
        # This transaction is false target with wrong account type
        # (only `Account.EXPENSE` accounts should be used for guessing)
        Transaction.objects.create(
            date=date.today(),
            account=cls.wrong_beer,
            amount=Decimal('124.56'),
            currency=RUB,
            comment=cls.wrong_beer_comment
        )

    def setUp(self):
        with open(self.invoice_path) as f:
            self.incoming = f.read()
        self.invoice = parse(self.incoming, self.user, self.expense,
                             self.account)

    def tearDown(self):
        del self.incoming
        self.invoice.delete()
        del self.invoice

    def test_total_sum(self):
        actual_sum = sum(i.amount for i in self.invoice.transactions.all())
        self.assertEqual(actual_sum, Decimal('0.00000'))

    def test_bad_total_sum(self):
        adjusted_incoming = json.loads(self.incoming)
        adjusted_incoming['items'].pop()

        with LogCapture() as l:
            result = parse(json.dumps(adjusted_incoming),
                           self.user, self.expense, self.account)

            l.check(
                ('accountant.misc.fns_parser',
                 'WARNING',
                 ('{} (id {}) is broken, total sum 618.89 is not equal'
                  ' to sum of items 493.99').format(
                     result, result.id
                 ))
            )

    def test_is_verified(self):
        self.assertTrue(self.invoice.is_verified)

    def test_items_number(self):
        self.assertEqual(len(self.invoice.transactions.all()), 9)

    def test_items_quantity(self):
        actual_quantities = [i.quantity for i in
                             self.invoice.transactions
                                 .order_by('quantity')
                                 .exclude(quantity=None)]
        expected_quantities = [Decimal('1.00000')] * 8

        self.assertEqual(actual_quantities, expected_quantities)

    def test_items_prices(self):
        actual_amounts = [i.amount for i in
                          self.invoice.transactions.order_by('amount')]
        expected_amounts = [
            Decimal('-618.89000'),
            Decimal('4.99000'),
            Decimal('56.00000'),
            Decimal('74.00000'),
            Decimal('74.00000'),
            Decimal('74.00000'),
            Decimal('97.00000'),
            Decimal('114.00000'),
            Decimal('124.90000')
        ]

        self.assertEqual(actual_amounts, expected_amounts)

    def test_items_comments(self):
        actual_comments = [i.comment for i in
                           self.invoice.transactions.order_by('comment')]
        expected_comments = sorted([
            '',
            'ЧИПСЫ LAY`S СО ВКУСОМ ПАПРИКИ',
            'ЧИПСЫ LAY`S КРАБ 150Г',
            'ЧИПСЫ LAY`S СМЕТАНА И ЗЕЛЕНЬ 1',
            'ПАКЕТ-МАЙКА ДИКСИ 38Х65 ПНД 12',
            'ПЕЧЕНЬЕ УШКИ С САХАРОМ 250Г Х/',
            'КОЛБАСА КРАКОВСКАЯ ДИВИНО П/К',
            self.beer_comment,
            self.wrong_beer_comment
        ])

        self.assertEqual(actual_comments, expected_comments)

    def test_account_guessing(self):
        self.assertEqual(
            len(self.invoice.transactions.filter(account=self.beer).all()),
            1
        )

    def test_unit_guessing(self):
        self.assertEqual(
            len(self.invoice.transactions.filter(unit='l').all()),
            1
        )

    def test_invoice_timestamp(self):
        self.assertEqual(
            self.invoice.timestamp,
            timezone('Europe/Moscow').localize(datetime(2017, 10, 15, 22, 38))
        )

    def test_transactions_date(self):
        expected_date = date(2017, 10, 15)
        for transaction in self.invoice.transactions.all():
            self.assertEqual(transaction.date, expected_date)

    def test_is_valid_invoice(self):
        self.assertTrue(is_valid_invoice(self.incoming))
