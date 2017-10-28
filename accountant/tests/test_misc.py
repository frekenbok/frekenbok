import json
from datetime import date
from decimal import Decimal
from os.path import abspath, dirname, join
from unittest import TestCase

from django.contrib.auth.models import User
from moneyed import RUB

from accountant.misc.fns_parser import parse
from accountant.models import Account, Transaction


class FnsInvoiceParserTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(
            username='james_t_kirk',
            email='captain@enterprise.com',
            password='tiberius'
        )
        cls.account = Account(title='Other', type=Account.EXPENSE)
        Account.add_root(instance=cls.account)
        cls.beer = Account(title='Beer', type=Account.EXPENSE)
        Account.add_root(instance=cls.beer)
        cls.wrong_beer = Account(title='Wrong beer', type=Account.ACCOUNT)
        Account.add_root(instance=cls.wrong_beer)

        cls.beer_comment = 'ПИВО ТРИ МЕДВЕДЯ СВЕТЛОЕ АЛК.4'
        cls.wrong_beer_comment = 'ПИВО ЧЕРНИГОВСКОЕ СВЕТЛОЕ АЛК.'
        # This transaction should be used to guess account for transaction
        Transaction.objects.create(
            date=date.today(),
            account=cls.beer,
            amount=Decimal('124.56'),
            currency=RUB,
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
        with open(
                join(dirname(abspath(__file__)), 'test_fns_invoice.json')) as f:
            self.incoming = f.read()
        self.invoice = parse(self.incoming, self.user, self.account)

    def tearDown(self):
        del self.incoming
        del self.invoice

    def test_total_sum(self):
        actual_sum = sum(i.amount for i in self.invoice.transactions.all())
        self.assertEqual(actual_sum, Decimal('618.89'))

    def test_failed_total_sum(self):
        adjusted_incoming = json.loads(self.incoming)
        adjusted_incoming['items'].pop()

        with self.assertRaises(ValueError):
            parse(json.dumps(adjusted_incoming), self.user, self.account)

    def test_items_number(self):
        self.assertEqual(len(self.invoice.transactions.all()), 8)

    def test_items_quantity(self):
        for transaction in self.invoice.transactions.all():
            self.assertEqual(transaction.quantity, Decimal('1'))

    def test_items_prices(self):
        actual_amounts = [i.amount for i in
                          self.invoice.transactions.order_by('amount')]
        expected_amounts = [
            Decimal('4.99'),
            Decimal('56.00'),
            Decimal('74.00'),
            Decimal('74.00'),
            Decimal('74.00'),
            Decimal('97.00'),
            Decimal('114.00'),
            Decimal('124.90')
        ]

        self.assertEqual(actual_amounts, expected_amounts)

    def test_items_comments(self):
        actual_comments = [i.comment for i in
                           self.invoice.transactions.order_by('comment')]
        expected_comments = sorted([
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