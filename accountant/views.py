from django.shortcuts import render
from django.views.generic import ListView, DetailView

from .models import Account, Transaction


class MainView(ListView):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/base.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.ACCOUNT)


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
