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

    def get_context_data(self, pk: int = None, **kwargs):
        if pk is not None:
            context = {
                'invoice': Invoice.objects.get(pk=pk),
                'transactions': Transaction.objects.filter(invoice=pk)
            }
        else:
            context = {'transactions': tuple(), 'invoice': None}
        # TODO There should be another way to get sorted tree
        context['accounts'] = Account.objects.order_by('tree_id', 'lft').all()
        context['base_currency'] = settings.BASE_CURRENCY
        return context

    @staticmethod
    def transaction_data_to_dict(data: tuple, invoice: Invoice=None):
        """
        Internal method used to transform tuple with transactions data to dict.
        See `InvoiceCreateOrEditView.get_transactions_data` source for details.
        :param invoice: invoice for returned transaction
        :param data: tuple with 6 elements
        :return: dict that can be used as kwarg for Transaction constructor
        """
        accounts = {i.pk: i for i in Account.objects.all()}
        return {
            'pk': int(data[0]) if data[0] else None,
            'date': parse(data[1]),
            'amount': Decimal(data[2].replace(',', '.').replace(' ', '')),
            'currency': get_currency(data[3]),
            'comment': data[4],
            'account': accounts[int(data[5])],
            'invoice': invoice
        }

    # noinspection PyCallByClass,PyArgumentList
    @staticmethod
    def get_transactions_data(request: HttpRequest, invoice: Invoice=None):
        """
        Method returns generator with dictionaries that can be used as kwarg
        for Transaction constructor
        :param invoice: it will be used as invoice for all returned transactions
        :param request: HttpRequest with proper formed POST
        :return: generator with dicts
        """
        return map(
            partial(InvoiceCreateOrEditView.transaction_data_to_dict,
                    invoice=invoice),
            filter(
                lambda x: x[1] and x[2] and x[3] and x[5],
                zip(
                    request.POST.getlist('transaction-id'),
                    request.POST.getlist('date'),
                    request.POST.getlist('amount'),
                    request.POST.getlist('currency'),
                    request.POST.getlist('comment'),
                    request.POST.getlist('account')
                )
            )
        )

    # noinspection PyCallByClass,PyArgumentList
    @transaction.atomic
    def post(self, request: HttpRequest, pk: int=None, *args, **kwargs):
        if request.POST.get('invoice-timestamp') and request.POST.get('invoice-comment'):
            invoice, created = Invoice.objects.update_or_create(
                pk=pk,
                timestamp=request.POST['invoice-timestamp'],
                comment=request.POST['invoice-comment'],
                user=request.user
            )

            for item in self.get_transactions_data(request, invoice):
                Transaction.objects.update_or_create(**item)

            return redirect(invoice.get_absolute_url())
        else:
            return self.get(request, *args, **kwargs)
