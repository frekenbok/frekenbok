from random import random

from accountant.models import Account, Sheaf
from moneyed import RUB, USD, EUR, GBP


def prepare_test_data(self):
    self.wallet = Account(title='Кошелёк', type=Account.ACCOUNT)
    Account.add_root(instance=self.wallet)
    for currency in (RUB, USD, EUR):
        Sheaf.objects.create(amount=int(random() * 100),
                             currency=currency,
                             account=self.wallet)

    self.reserve = Account(title='Заначка', type=Account.ACCOUNT)
    Account.add_root(instance=self.reserve)

    for currency in (RUB, USD, GBP):
        Sheaf.objects.create(amount=int(random() * 100),
                             currency=currency,
                             account=self.reserve)

    # Test income
    self.exante = Account(title='Exante', type=Account.INCOME)
    Account.add_root(instance=self.exante)
    self.exante = Account.objects.get(pk=self.exante.pk)
    self.salary = self.exante.add_child(title='Зарплата', type=Account.INCOME)
    self.salary = Account.objects.get(pk=self.salary.pk)
    self.bonus = self.exante.add_child(title='Премия', type=Account.INCOME)

    # Test expenses
    self.expenses = [
        Account(title=expense, type=Account.EXPENSE)
        for expense in ('Бензин', 'Хлеб', 'Колбаса')
        ]
    for expense in self.expenses:
        Account.add_root(instance=expense)