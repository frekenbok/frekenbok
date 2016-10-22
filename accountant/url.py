from django.conf.urls import url
from django.contrib import admin

from .views import DashboardView, IncomeListView, AccountDetailView, \
    AccountListView

urlpatterns = [
    url(r'^$', DashboardView.as_view(), name='dashboard'),
    url(r'^incomes/', IncomeListView.as_view(), name='income_list'),
    url(r'^accounts/(?P<pk>[0-9]+)/', AccountDetailView.as_view(), name='account_detail'),
    url(r'^accounts/', AccountListView.as_view(), name='account_list'),
    url(r'^expenses/', IncomeListView.as_view(), name='expense_list'),
]
