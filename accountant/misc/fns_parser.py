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
def parse(raw_invoice: str, user: User, default_account: Account):
    invoice = json.loads(raw_invoice, parse_float=Decimal, parse_int=Decimal)

    timestamp = datetime.fromtimestamp(invoice['dateTime'])
    total_sum = Money(invoice['totalSum'] / divisor, currency)

    result = Invoice.objects.create(
        timestamp=timestamp,
        comment='{} ({})'.format(invoice['user'], total_sum),
        user=user
    )

    for item in invoice['items']:
        comment = item['name']
        maybe_transaction = Transaction.objects.filter(
            comment=comment,
            account__in=Account.get_expenses()
        ).first()
        if maybe_transaction:
            account = maybe_transaction.account
        else:
            account = default_account

        Transaction.objects.create(
            date=timestamp.date(),
            account=account,
            amount=item['sum'] / divisor,
            currency=currency,
            quantity=item['quantity'],
            invoice=result,
            comment=comment
        )

    sum_of_items = sum(i.amount for i in result.transactions.all())
    if sum_of_items != total_sum.amount:
        raise ValueError(
            'Invoice is broken, total sum {} is not equal to sum of items {}'
            .format(total_sum.amount, sum_of_items)
        )

    return result
