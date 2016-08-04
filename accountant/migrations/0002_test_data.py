# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from moneyed import RUB, USD, EUR

from accountant.models import Account


def create_accounts(apps, schema_editor):
    account_model = apps.get_model('accountant', 'Account')
    sheaf_model = apps.get_model('accountant', 'Sheaf')
    wallet = account_model.objects.create(title='Кошелёк', type=Account.ACCOUNT)
    for currency in (RUB, USD, EUR):
        sheaf_model.objects.create(amount=10, currency=currency, account=wallet)

    salary = account_model.objects.create(title='Зарплата в Exante', type=Account.INCOME)

    for expence in ('Бензин', 'Хлеб', 'Колбаса'):
        account_model.objects.create(title=expence, type=Account.EXPENSE)

class Migration(migrations.Migration):

    dependencies = [
        ('accountant', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_accounts
        )
    ]
