# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from random import random
from datetime import datetime, date
from decimal import Decimal

from django.db import migrations
from moneyed import Money, RUB, USD, EUR, GBP

from accountant.models import Account


def add_test_data(apps, schema_editor):
    account_model = apps.get_model('accountant', 'Account')
    sheaf_model = apps.get_model('accountant', 'Sheaf')

    # Test accounts
    wallet = account_model(title='Кошелёк', type=Account.ACCOUNT)
    Account.add_root(instance=wallet)
    for currency in (RUB, USD, EUR):
        sheaf_model.objects.create(amount=int(random() * 100),
                                   currency=currency,
                                   account=wallet)

    reserve = account_model(title='Заначка', type=Account.ACCOUNT)
    Account.add_root(instance=reserve)

    for currency in (RUB, USD, GBP):
        sheaf_model.objects.create(amount=int(random() * 100),
                                   currency=currency,
                                   account=reserve)

    # Test income
    exante = account_model(title='Exante', type=Account.INCOME)
    Account.add_root(instance=exante)
    exante = Account.objects.get(pk=exante.pk)
    salary = exante.add_child(title='Зарплата', type=Account.INCOME)
    salary = account_model.objects.get(pk=salary.pk)
    bonus = exante.add_child(title='Премия', type=Account.INCOME)

    # Test expenses
    expenses = [
        account_model(title=expense, type=Account.EXPENSE)
        for expense in ('Бензин', 'Хлеб', 'Колбаса')
    ]
    for expense in expenses:
        Account.add_root(instance=expense)

    transaction_model = apps.get_model('accountant', 'Transaction')
    invoice_model = apps.get_model('accountant', 'Invoice')

    # Test income
    first_salary = invoice_model.objects.create(timestamp=datetime(2015, 4, 1))
    transaction_model.objects.create(
        date=date(2015, 4, 1),
        account=salary,
        amount=Decimal(-70000),
        currency=RUB,
        invoice=first_salary,
    )
    transaction_model.objects.create(
        date=date(2015, 4, 1),
        account=wallet,
        amount=Decimal(70000),
        currency=RUB,
        invoice=first_salary
    )

    first_invoice = invoice_model.objects.create(timestamp=datetime(2015, 4, 3))
    sum_of_first_invoice = Decimal(0)
    for expense in expenses:
        value = int(random() * 100)
        sum_of_first_invoice += value
        transaction_model.objects.create(
            date=date(2015, 4, 3),
            account=expense,
            amount=value,
            currency=RUB,
            invoice=first_invoice
        )
    transaction_model.objects.create(
        date=date(2015, 4, 3),
        account=wallet,
        amount=-sum_of_first_invoice,
        currency=RUB,
        invoice=first_invoice
    )

    second_invoice = invoice_model.objects.create(timestamp=datetime(2015, 4, 4))
    value = int(random() * 100)
    transaction_model.objects.create(
        date=date(2015, 4, 4),
        account=wallet,
        amount=-value,
        currency=RUB,
        invoice=second_invoice,
        comment='салями'
    )
    transaction_model.objects.create(
        date=date(2015, 4, 4),
        account=expenses[-1],
        amount=value,
        currency=RUB,
        invoice=second_invoice,
        comment='салями'
    )

    third_invoice = invoice_model.objects.create(timestamp=datetime(2015, 4, 5))
    value = int(random() * 100)
    transaction_model.objects.create(
        date=date(2015, 4, 5),
        account=wallet,
        amount=-value,
        currency=RUB,
        invoice=third_invoice,
        comment='АИ-95'
    )
    transaction_model.objects.create(
        date=date(2015, 4, 5),
        account=expenses[0],
        amount=value,
        currency=RUB,
        invoice=third_invoice,
        comment='АИ-95'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accountant', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            add_test_data
        ),
    ]
