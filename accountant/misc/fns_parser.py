import json
import logging
from datetime import datetime
from decimal import Decimal

import pytz
from django.contrib.auth.models import User
from django.db import transaction
from moneyed import RUB, Money

from accountant.models import Invoice, Transaction, Account

logger = logging.getLogger(__name__)

divisor = Decimal(100)
currency = RUB
tz = pytz.timezone('Europe/Moscow')


def is_valid_invoice(raw_invoice: str):
    invoice = json.loads(raw_invoice, parse_float=Decimal, parse_int=Decimal)
    return isinstance(invoice.get('items'), list) and \
        isinstance(invoice.get('totalSum'), Decimal) and \
        invoice.get('fiscalDocumentNumber') and \
        invoice.get('fiscalDriveNumber') and \
        invoice.get('fiscalSign')


@transaction.atomic
def parse(raw_invoice: str, user: User,
          default_expense: Account, default_account: Account):
    invoice = json.loads(raw_invoice, parse_float=Decimal, parse_int=Decimal)

    timestamp = datetime.fromtimestamp(invoice['dateTime'], tz)
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

    sum_of_items = Decimal(0)
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

        item_price = item['sum'] / divisor
        Transaction.objects.create(
            date=date,
            account=account,
            amount=item_price,
            currency=currency,
            quantity=item['quantity'],
            unit=unit,
            invoice=result,
            comment=comment
        )
        sum_of_items += item_price

    if sum_of_items != total_sum:
        logger.warning(
            '{} (id {}) is broken, total sum {} is not equal to sum of items {}'
            .format(result, result.id, total_sum, sum_of_items)
        )

    return result
