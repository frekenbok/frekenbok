import logging
from decimal import Decimal
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.conf import settings

from .models import Account, Transaction


class MainView(ListView):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/base.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.ACCOUNT)

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data(**kwargs)

        total = dict()
        for account in context['account_list']:
            for sheaf in account.sheaves.all():
                total.setdefault(sheaf.currency, Decimal('0'))
                total[sheaf.currency] += sheaf.amount

        # Generating report about total value of all accounts and
        # placing value in base currency to first place in that report
        report = list()
        base_currency_amount = total.get(settings.BASE_CURRENCY)
        print('There is base currency {bc} in total report ({amount})'
                      .format(bc=settings.BASE_CURRENCY,
                              amount=base_currency_amount))
        if base_currency_amount:
            report.append({'currency': settings.BASE_CURRENCY,
                           'amount': base_currency_amount})
            del total[settings.BASE_CURRENCY]
        for currency, amount in sorted(total.items(), key=lambda x: x[0]):
            report.append({'currency': currency, 'amount': amount})

        context['total'] = report
        return context


class IncomeListView(ListView):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/account_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.INCOME)


class AccountDetailView(DetailView):
    model = Account
    context_object_name = 'account'
    template_name = 'accountant/account_detail.html'


class TransactionListView(ListView):
    model = Transaction
    context_object_name = 'transaction'
