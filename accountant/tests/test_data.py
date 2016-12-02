from random import random
from datetime import date, datetime
from decimal import Decimal

from accountant.models import Account, Sheaf, Invoice, Transaction
from moneyed import RUB, USD, EUR, GBP


def add_test_data(cls):
    # Test accounts
    cls.wallet = Account(title='Кошелёк', type=Account.ACCOUNT)
    Account.add_root(instance=cls.wallet)
    for currency in (RUB, EUR):
        Sheaf.objects.create(amount=int(random() * 100),
                             currency=currency,
                             account=cls.wallet)

    cls.reserve = Account(title='Заначка', type=Account.ACCOUNT)
    Account.add_root(instance=cls.reserve)

    for currency in (RUB, USD, GBP):
        Sheaf.objects.create(amount=int(random() * 100),
                             currency=currency,
                             account=cls.reserve)

    # Test income
    job = Account(title='Exante', type=Account.INCOME)
    Account.add_root(instance=job)
    cls.job = Account.objects.get(pk=job.pk)
    salary = cls.job.add_child(title='Зарплата', type=Account.INCOME)
    cls.salary = Account.objects.get(pk=salary.pk)
    cls.bonus = cls.job.add_child(title='Премия', type=Account.INCOME)

    # Test expenses
    cls.expenses = [
        Account(title=expense, type=Account.EXPENSE)
        for expense in ('Бензин', 'Хлеб', 'Колбаса')
    ]
    for expense in cls.expenses:
        Account.add_root(instance=expense)

    # Test income
    cls.first_salary = Invoice.objects.create(timestamp=datetime(2015, 4, 1))
    Transaction.objects.create(
        date=date(2015, 4, 1),
        account=cls.salary,
        amount=Decimal(-70000),
        currency=RUB,
        invoice=cls.first_salary,
    )
    Transaction.objects.create(
        date=date(2015, 4, 1),
        account=cls.wallet,
        amount=Decimal(70000),
        currency=RUB,
        invoice=cls.first_salary
    )

    cls.first_bonus = Invoice.objects.create(timestamp=datetime(2015, 4, 2))
    Transaction.objects.create(
        date=date(2015, 4, 2),
        account=cls.bonus,
        amount=Decimal(-200),
        currency=USD,
        invoice=cls.first_bonus
    )
    Transaction.objects.create(
        date=date(2015, 4, 2),
        account=cls.wallet,
        amount=Decimal(200),
        currency=USD,
        invoice=cls.first_bonus
    )

    # Test expenses
    cls.first_invoice = Invoice.objects.create(timestamp=datetime(2015, 4, 3))
    sum_of_first_invoice = Decimal(0)
    for expense in cls.expenses:
        value = int(random() * 100)
        sum_of_first_invoice += value
        Transaction.objects.create(
            date=date(2015, 4, 3),
            account=expense,
            amount=value,
            currency=RUB,
            invoice=cls.first_invoice
        )
    Transaction.objects.create(
        date=date(2015, 4, 3),
        account=cls.wallet,
        amount=-sum_of_first_invoice,
        currency=RUB,
        invoice=cls.first_invoice
    )

    cls.second_invoice = Invoice.objects.create(timestamp=datetime(2015, 4, 4))
    value = int(random() * 100)
    Transaction.objects.create(
        date=date(2015, 4, 4),
        account=cls.wallet,
        amount=-value,
        currency=RUB,
        invoice=cls.second_invoice,
        comment='салями'
    )
    Transaction.objects.create(
        date=date(2015, 4, 4),
        account=cls.expenses[-1],
        amount=value,
        currency=RUB,
        invoice=cls.second_invoice,
        comment='салями'
    )

    cls.third_invoice = Invoice.objects.create(timestamp=datetime(2015, 4, 5))
    value = int(random() * 100)
    Transaction.objects.create(
        date=date(2015, 4, 5),
        account=cls.wallet,
        amount=-value,
        currency=RUB,
        invoice=cls.third_invoice,
        comment='АИ-95'
    )
    Transaction.objects.create(
        date=date(2015, 4, 5),
        account=cls.expenses[0],
        amount=value,
        currency=RUB,
        invoice=cls.third_invoice,
        comment='АИ-95'
    )
