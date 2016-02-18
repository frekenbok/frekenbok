from django.shortcuts import render
from django.views.generic import ListView, DetailView

from .models import Account, Transaction


class AccountListView(ListView):
    model = Account
    context_object_name = 'account_list'


class AccountDetailView(DetailView):
    model = Account
    context_object_name = 'account'


class TransactionListView(ListView):
    model = Transaction
    context_object_name = 'transaction'
