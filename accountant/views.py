import re
import json
import logging
from datetime import date, datetime
from decimal import Decimal

import pytz

from django.db.models import F, Q
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView
from django.views.generic.base import ContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import JsonResponse, HttpResponse

from .models import Account, Transaction, Invoice


logger = logging.getLogger(__name__)


sms_parsers = {
    'Tinkoff': {
        'regexp': re.compile(
            r'(?P<action>[\w ]+)\. (?P<account>[\w *_]+)\. '
            r'Summa (?P<amount>[\d\.]+) (?P<currency>[A-Z]{3})\. '
            r'(?P<receiver>[\w ,.]+)\. (?P<datetime>[0-9. :]{16})\. '
            r'Dostupno (?P<rest_amount>[\d.]+) (?P<rest_currency>[A-Z]{3})\.',
            re.ASCII),
        'negative_actions': {'Pokupka', 'Snytie nalichnyh', 'Platezh',
                             'Operatsia v drugih kreditnyh organizatsiyah',
                             'Vnutrenniy perevod sebe', 'Vneshniy perevod'},
        'datetime_format': '%d.%m.%Y %H:%M',
        'datetime_tz': pytz.timezone('Europe/Moscow')
    }
}


class AccountantViewMixin(LoginRequiredMixin, ContextMixin):
    raise_exception = True

    def get_context_data(self, **kwargs):
        result = super(AccountantViewMixin, self).get_context_data(**kwargs)
        result['accountant_app'] = True
        return result


class DashboardView(ListView, AccountantViewMixin):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/dashboard.html'

    def get_queryset(self):
        '''
        Dashboard displays all accounts with Account.ACCOUNT type and without
        child accounts. Child free items in nested set can be found by
        :return:
        '''
        return self.model.objects\
            .filter(type=Account.ACCOUNT, lft__exact=F('rgt') - 1)\
            .filter(Q(closed__gte=date.today()) | Q(closed=None))

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)

        total = dict()
        for account in context['account_list']:
            for sheaf in account.sheaves.all():
                total.setdefault(sheaf.currency, Decimal('0'))
                total[sheaf.currency] += sheaf.amount

        # Generating report about total value of all accounts and
        # placing value in base currency to first place in that report
        total_report = list()
        for currency, amount in sorted(total.items(), key=lambda x: x[0]):
            report_line = {'currency': currency, 'amount': amount}
            if currency == settings.BASE_CURRENCY:
                total_report.insert(0, report_line)
            else:
                total_report.append(report_line)

        overview = list()
        for account in self.model.objects.filter(type=Account.ACCOUNT, depth=1):
            report = account.tree_summary()
            overview.append({'account': account.title,
                             'report': report,
                             'weight': sum(i['amount'] for i in report),
                             # TODO We should try to guess currency here
                             'weight_currency': settings.BASE_CURRENCY})

        context['overview'] = overview
        context['total'] = total_report
        context['menu_dashboard'] = True
        return context


class AccountListView(ListView, AccountantViewMixin):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/account_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.ACCOUNT) \
            .filter(Q(closed__gte=date.today()) | Q(closed=None))


class IncomeListView(ListView, AccountantViewMixin):
    model = Account
    context_object_name = 'income_list'
    template_name = 'accountant/income_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.INCOME) \
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


@require_http_methods(['POST'])
def sms(request):
    message = json.loads(request.body.decode())
    logger.info('Received SMS {}'.format(message))

    if message['secret'] != settings.SMS_SECRET_KEY:
        logger.error('Unauthorized attempts to send SMS, received secret key {}'
                     .format(message['secret']))
        return HttpResponse('Unauthorized', status=401)

    try:
        parser = sms_parsers[message['from']]
    except KeyError:
        logger.error('Sender {} not found in parser config'
                     .format(message['from']))
        return JsonResponse({'status': 'error', 'message': 'Unknown sender'},
                            status=404)

    regexp = parser['regexp']
    parsed_message = regexp.search(message['message']).groupdict()

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
            comment=message['message']
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
