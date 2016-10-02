# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from random import random
from datetime import datetime, date

from django.db import migrations
from moneyed import Money, RUB, USD, EUR, GBP

from accountant.models import Account


def add_test_data(apps, schema_editor):
    account_model = apps.get_model('accountant', 'Account')
    sheaf_model = apps.get_model('accountant', 'Sheaf')

    wallet = account_model.objects.create(title='Кошелёк',
                                          type=Account.ACCOUNT)
    for currency in (RUB, USD, EUR):
        sheaf_model.objects.create(amount=int(random() * 100),
                                   currency=currency,
                                   account=wallet)

    reserve = account_model.objects.create(title='Заначка',
                                           type=Account.ACCOUNT)
    for currency in (RUB, USD, GBP):
        sheaf_model.objects.create(amount=int(random() * 100),
                                   currency=currency,
                                   account=reserve)

    salary = account_model.objects.create(title='Зарплата в Exante',
                                          type=Account.INCOME)

    expenses = [
        account_model.objects.create(title=expense, type=Account.EXPENSE)
            for expense in ('Бензин', 'Хлеб', 'Колбаса')
    ]

    transaction_model = apps.get_model('accountant', 'Transaction')
    invoice_model = apps.get_model('accountant', 'Invoice')

    first_salary = invoice_model.objects.create(timestamp=datetime(2015, 4, 1))
    transaction_model.objects.create(
        source=salary,
        source_value=Money(70000, RUB),
        destination=wallet,
        destination_value=Money(70000, RUB),
        invoice=first_salary,
        date=date(2015, 4, 1)
    )

    first_invoice = invoice_model.objects.create(timestamp=datetime(2015, 4, 3))
    for expense in expenses:
        value = int(random() * 100) + int(random() * 100) / 100
        transaction_model.objects.create(
            date=date(2015, 4, 3),
            source=wallet,
            source_value=Money(value, RUB),
            destination=expense,
            destination_value=Money(value, RUB),
            invoice=first_invoice
        )

    second_invoice = invoice_model.objects.create(timestamp=datetime(2015, 4, 4))
    for expense in expenses[:-1]:
        value = int(random() * 100) + int(random() * 100) / 100
        transaction_model.objects.create(
            date=date(2015, 4, 4),
            source=wallet,
            source_value=Money(value, RUB),
            destination=expense,
            destination_value=Money(value, RUB),
            invoice=second_invoice,
            comment='салями'
        )

    third_invoice = invoice_model.objects.create(timestamp=datetime(2015, 4, 5))
    for expense in expenses[1:]:
        value = int(random() * 100) + int(random() * 100) / 100
        transaction_model.objects.create(
            date=date(2015, 4, 5),
            source=wallet,
            source_value=Money(value, RUB),
            destination=expense,
            destination_value=Money(value, RUB),
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
