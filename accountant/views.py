from django.shortcuts import render
from django.views.generic import ListView, DetailView

from .models import Account, Transaction


def main(request):
    context = dict()
    for account_type in ('income', 'account', 'expense'):
        query_set = Account.objects.filter(type=account_type)
        context[account_type] = query_set if query_set else []
    return render(request, 'accountant/base.html', context)


class IncomeListView(ListView):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/account_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type='income')


class AccountDetailView(DetailView):
    model = Account
    context_object_name = 'account'
    template_name = 'accountant/account_detail.html'


class TransactionListView(ListView):
    model = Transaction
    context_object_name = 'transaction'
