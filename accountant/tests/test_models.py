from random import random

from django.test import TestCase
from moneyed import RUB, USD, EUR, GBP

from accountant.models import Account, Sheaf
from .test_data import prepare_test_data


class AccountTestCase(TestCase):
    def setUp(self):
        prepare_test_data(self)

    def test_sorted_sheaves(self):
        self.assertEqual(
            [i.currency for i in self.wallet.sorted_sheaves],
            ['RUB', 'EUR', 'USD']
        )
