import json
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from moneyed import RUB, Money

from accountant.models import Invoice, Transaction, Account

divisor = Decimal(100)
currency = RUB


@transaction.atomic
def parse(raw_invoice: str, user: User,
          default_expense: Account, default_account: Account):
    invoice = json.loads(raw_invoice, parse_float=Decimal, parse_int=Decimal)

    timestamp = datetime.fromtimestamp(invoice['dateTime'])
    date = timestamp.date()
    total_sum = invoice['totalSum'] / divisor

    result = Invoice.objects.create(
        timestamp=timestamp,
        comment='{} ({})'.format(invoice['user'], Money(total_sum, currency)),
        user=user
    )

    Transaction.objects.create(
        date=date,
        account=default_account,
        amount=-total_sum,
        currency=currency,
        invoice=result
    )

    for item in invoice['items']:
        comment = item['name']
        maybe_transaction = Transaction.objects.filter(
            comment=comment,
            account__in=Account.get_expenses()
        ).first()
        if maybe_transaction:
            account = maybe_transaction.account
            unit = maybe_transaction.unit
        else:
            account = default_expense
            unit = None

        Transaction.objects.create(
            date=date,
            account=account,
            amount=item['sum'] / divisor,
            currency=currency,
            quantity=item['quantity'],
            unit=unit,
            invoice=result,
            comment=comment
        )

    sum_of_items = sum(i.amount for i in result.transactions.all())
    if sum_of_items != Decimal(0):
        raise ValueError(
            'Invoice is broken, total sum {} is not equal to sum of items {}'
            .format(total_sum, sum_of_items)
        )

    return result
