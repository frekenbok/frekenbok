from django.conf.urls import url
from django.contrib import admin

from .views import DashboardView, IncomeListView, AccountDetailView

urlpatterns = [
    url(r'^$', DashboardView.as_view(), name='main'),
    url(r'^incomes/', IncomeListView.as_view(), name='income_list'),
    url(r'^accounts/', IncomeListView.as_view(), name='account_list'),
    url(r'^expenses/', IncomeListView.as_view(), name='expense_list'),
    url(r'^details/(?P<pk>[0-9]+)', AccountDetailView.as_view(), name='account_details'),
]
