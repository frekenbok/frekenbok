import logging
from datetime import date, datetime
from decimal import Decimal

from django.db.models import Q
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView
from django.views.generic.base import ContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpRequest

from .models import Account, Transaction, Invoice


logger = logging.getLogger(__name__)


class AccountantViewMixin(LoginRequiredMixin, ContextMixin):
    def get_context_data(self, **kwargs):
        result = super(AccountantViewMixin, self).get_context_data(**kwargs)
        result['accountant_app'] = True
        return result


class AccountListView(ListView, AccountantViewMixin):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/account_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.ACCOUNT) \
            .filter(Q(closed__gte=date.today()) | Q(closed=None))


class IncomeListView(ListView, AccountantViewMixin):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/account_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.INCOME) \
            .filter(Q(closed__gte=date.today()) | Q(closed=None))


class ExpenseListView(ListView, AccountantViewMixin):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/account_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.EXPENSE) \
            .filter(Q(closed__gte=date.today()) | Q(closed=None))


class AccountDetailView(DetailView, AccountantViewMixin):
    model = Account
    context_object_name = 'account'
    template_name = 'accountant/account_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AccountDetailView, self).get_context_data(**kwargs)
        if context['account'].type == Account.ACCOUNT:
            context['account_list'] = \
                self.model.objects.filter(type=Account.ACCOUNT)\
                    .filter(Q(closed__gte=date.today()) | Q(closed=None)).all()
        context['transaction_list'] = \
            Transaction.objects.filter(account=self.object)\
                .order_by('-date')[:10]
        return context


class TransactionListView(ListView):
    model = Transaction
    context_object_name = 'transaction'


class InvoiceListView(ListView, AccountantViewMixin):
    model = Invoice
    context_object_name = 'invoice_list'
    template_name = 'accountant/invoice_list.html'
    paginate_by = 20


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
