from django.conf.urls import url
from django.contrib import admin

from .views import AccountListView, AccountDetailView, TransactionListView

urlpatterns = [
    url(r'^accounts/', AccountListView.as_view(), name='account_list'),
    url(r'^accounts/(?P<pk>[0-9]+)', AccountListView.as_view()),
]
