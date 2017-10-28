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
        Transaction.objects.create(
            date=timestamp.date(),
            account=default_account,
            amount=item['sum'] / divisor,
            currency=currency,
            quantity=item['quantity'],
            invoice=result,
            comment=item['name']
        )

    pnl_amount = result.pnl[0]['amount']
    if pnl_amount != total_sum.amount:
        raise ValueError(
            'Invoice is broken, total sum {} is not equal to sum of items {}'
            .format(total_sum.amount, pnl_amount)
        )

    return result
