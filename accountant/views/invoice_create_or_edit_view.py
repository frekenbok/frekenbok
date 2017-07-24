import logging

from decimal import Decimal
from functools import partial

from django.shortcuts import redirect
from moneyed import get_currency
from dateutil.parser import parse

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpRequest
from django.views.generic.base import TemplateView

from accountant.models import Invoice, Account, Transaction

logger = logging.getLogger(__name__)


class InvoiceCreateOrEditView(LoginRequiredMixin, TemplateView):
    template_name = 'accountant/invoice_create_or_edit.html'

    def __init__(self, **kwargs):
        super(InvoiceCreateOrEditView, self).__init__(**kwargs)
        self.accounts = {i.pk: i for i in Account.objects.all()}

    def get_context_data(self, pk: int = None, **kwargs):
        if pk is not None:
            context = {
                'invoice': Invoice.objects.get(pk=pk),
                'transactions': Transaction.objects.filter(invoice=pk),
                'quantity_units': Transaction.UNITS
            }
        else:
            context = {'transactions': tuple(), 'invoice': None}
        # TODO There should be another way to get sorted tree
        context['accounts'] = Account.objects.order_by('tree_id', 'lft').all()
        context['base_currency'] = settings.BASE_CURRENCY
        return context

    def transaction_data_to_dict(self, data: tuple, invoice: Invoice=None):
        """
        Internal method used to transform tuple with transactions data to dict.
        See `InvoiceCreateOrEditView.get_transactions_data` source for details.
        :param invoice: invoice for returned transaction
        :param data: tuple with 6 elements
        :return: tuple that can be used for Transaction create_or_update method
        """
        return (
            int(data[0]) if data[0] else None,
            {
                'date': parse(data[1]).date(),
                'amount': Decimal(data[2].replace(',', '.').replace(' ', '')),
                'currency': get_currency(data[3]),
                'quantity': Decimal(data[4].replace(',', '.').replace(' ', '')),
                'unit': data[5],
                'comment': data[6],
                'account': self.accounts[int(data[7])],
                'invoice': invoice
            }
        )

    # noinspection PyCallByClass,PyArgumentList
    def get_transactions_data(self, request: HttpRequest, invoice: Invoice=None):
        """
        Method returns generator with tuples that can be used for
         create_or_update method.
        :param invoice: it will be used as invoice for all returned transactions
        :param request: HttpRequest with proper formed POST
        :return: generator with tuples
        """
        self.accounts = {i.pk: i for i in Account.objects.all()}
        return map(
            partial(self.transaction_data_to_dict, invoice=invoice),
            filter(
                lambda x: x[1] and x[2] and x[3] and x[7],
                zip(
                    request.POST.getlist('transaction-id'),
                    request.POST.getlist('date'),
                    request.POST.getlist('amount'),
                    request.POST.getlist('currency'),
                    request.POST.getlist('quantity'),
                    request.POST.getlist('unit'),
                    request.POST.getlist('comment'),
                    request.POST.getlist('account')
                )
            )
        )

    # noinspection PyCallByClass,PyArgumentList
    @transaction.atomic
    def post(self, request: HttpRequest, pk: int=None, *args, **kwargs):
        logger.debug('Trying to create or update invoice with pk {}'.format(pk))
        logger.debug('Timestamp {}, comment {}'.format(request.POST.get('invoice-timestamp'), request.POST.get('invoice-comment')))
        if request.POST.get('invoice-timestamp'):
            invoice, created = Invoice.objects.update_or_create(
                pk=int(pk) if pk else None,
                defaults={
                    'timestamp': parse(request.POST['invoice-timestamp']),
                    'comment': request.POST['invoice-comment'],
                    'user': request.user
                }
            )
            logger.debug('Invoice {} was {}'.format(invoice, 'created' if created else 'found'))

            for pk, defaults in self.get_transactions_data(request, invoice):
                tx, created = Transaction.objects.update_or_create(
                    pk=pk, defaults=defaults
                )
                logger.debug('Transaction {} was {}'.format(tx, 'created' if created else 'found'))

            return redirect(invoice.get_absolute_url())
        else:
            return self.get(request, *args, **kwargs)
