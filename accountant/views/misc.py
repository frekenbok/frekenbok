import logging
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from accountant.models import Account, Invoice, Transaction, Document

logger = logging.getLogger(__name__)


@csrf_exempt
def sms(request: HttpRequest):
    message = request.GET
    logger.info('Received SMS {}'.format(message))

    if message.get('secret') != settings.SMS_SECRET_KEY:
        logger.error('Unauthorized attempts to send SMS, received secret key {}'
                     .format(message.get('secret')))
        return HttpResponse('Unauthorized', status=401)

    try:
        parser = settings.SMS_PARSERS[message['phone']]
    except KeyError:
        logger.error('Sender {} not found in parser config'
                     .format(message['phone']))
        return JsonResponse({'status': 'error', 'message': 'Unknown sender'},
                            status=404)

    regexp = parser['regexp']
    parsed_message = regexp.search(message['text']).groupdict()

    account = Account.objects.filter(bank_title=parsed_message['account']).first()
    if account is None:
        logger.error('Account with bank_title {} not found'
                     .format(parsed_message['account']))
        return JsonResponse({'status': 'error', 'message': 'Unknown account'},
                            status=404)

    amount = Decimal(parsed_message['amount'])
    if parsed_message['action'] in parser['negative_actions']:
        amount *= -1
    timestamp = parser['datetime_tz'].localize(
        datetime.strptime(
            parsed_message['datetime'],
            parser['datetime_format']
        )
    )

    with transaction.atomic():
        invoice = Invoice.objects.create(
            timestamp=timestamp,
            comment=message['text']
        )
        new_transaction = Transaction.objects.create(
            invoice=invoice,
            date=timestamp.date(),
            account=account,
            amount=amount,
            currency=parsed_message['currency'],
            comment=parsed_message['receiver']
        )

    logger.info('Added invoice {} and transaction {}'
                .format(invoice, new_transaction))
    return JsonResponse({'status': 'ok',
                         'invoice': invoice.pk,
                         'transaction': new_transaction.pk})


@transaction.atomic
def recalculate_request(request: HttpRequest):
    for account in Account.objects.all():
        account.recalculate_summary(atomic=False)
    return redirect(
        request.META.get('HTTP_REFERER', reverse('accountant:account_list'))
    )


@csrf_exempt
def document_upload(request: HttpRequest):
    file = request.FILES.get('file')
    document = Document.objects.create(
        description='',
        invoice=None,
        file=file
    )
    return JsonResponse({
        'id': document.id,
        'description': document.description,
        'invoice': document.invoice,
    })


def document_delete(request: HttpRequest):
    pass