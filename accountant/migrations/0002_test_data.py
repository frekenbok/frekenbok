# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal
from django.db import migrations
from moneyed import Money, RUB, USD, EUR

from accountant.models import Account


def create_accounts(apps, schema_editor):
    account_model = apps.get_model('accountant', 'Account')
    test_accounts = (
        {'title': 'Кошелёк', 'type': Account.ACCOUNT, 'value': Money(0, RUB)},
        {'title': 'Tinkoff RUB', 'type': Account.ACCOUNT, 'value': Money(0, RUB)},
        {'title': 'Tinkoff USD', 'type': Account.ACCOUNT, 'value': Money(0, USD)},
        {'title': 'Tinkoff EUR', 'type': Account.ACCOUNT, 'value': Money(0, EUR)},
    )
    for account in test_accounts:
        account_model.objects.create(**account)

    test_incomes = (
        {'title': 'Белая зарплата', 'type': Account.INCOME, 'value': Money(0, RUB)},
        {'title': 'Серая зарплата', 'type': Account.INCOME, 'value': Money(0, RUB)},
    )
    for income in test_incomes:
        account_model.objects.create(**income)
    interest_rates = account_model.objects.create(
        title='Проценты по вкладам',
        type=Account.INCOME,
        value=Money(0, RUB)
    )
    account_model.objects.create(
        title='Tinkoff RUB',
        type=Account.INCOME,
        value=Money(0, RUB),
        parent=interest_rates
    )


class Migration(migrations.Migration):

    dependencies = [
        ('accountant', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_accounts
        )
    ]