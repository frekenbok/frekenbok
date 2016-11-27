from django.test import TestCase
from django.conf import settings

from autofixture import AutoFixture

from accountant.models import Account, Sheaf


class AccountTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.accounts = AutoFixture(Account).create(30)
        for account in cls.accounts:
            AutoFixture(Sheaf, field_values={'account': account}).create(3)

    def test_sorted_sheaves(self):
        currencies = [i.currency for i in self.accounts[0].sheaves.all()]

        self.assertEqual(currencies[0], settings.BASE_CURRENCY)

        self.assertEqual(
            currencies[1:],
            sorted(currencies[1:])
        )
