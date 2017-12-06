from django.conf.urls import url, include

from accountant.views.misc import sms, recalculate_request, document_upload, \
    document_delete
from accountant.views.invoice_create_or_edit_view import InvoiceCreateOrEditView
from accountant.views.invoice_detail_view import InvoiceDetailView
from accountant.views.invoice_list_view import InvoiceListView
from accountant.views.account_detail_view import AccountDetailView
from accountant.views.income_list_view import IncomeListView
from accountant.views.expense_list_view import ExpenseListView
from accountant.views.account_list_view import AccountListView
from accountant.views.statement_import_view import StatementImportView

urlpatterns = [
    url(r'^incomes/', IncomeListView.as_view(), name='income_list'),
    url(r'^accounts/(?P<pk>[0-9]+)/', AccountDetailView.as_view(), name='account_detail'),
    url(r'^accounts/', AccountListView.as_view(), name='account_list'),
    url(r'^incomes/', IncomeListView.as_view(), name='income_list'),
    url(r'^expenses/', ExpenseListView.as_view(), name='expense_list'),
    url(r'^invoices/add/', InvoiceCreateOrEditView.as_view(), name='invoice_create'),
    url(r'^invoices/(?P<pk>[0-9]+)/edit/', InvoiceCreateOrEditView.as_view(), name='invoice_edit'),
    url(r'^invoices/(?P<pk>[0-9]+)/', InvoiceDetailView.as_view(), name='invoice_detail'),
    url(r'^invoices/', InvoiceListView.as_view(), name='invoice_list'),
    url(r'^sms/', sms, name='sms'),
    url(r'^recalculate/', recalculate_request, name='recalculate'),
    url(r'^document/upload', document_upload, name='document_upload'),
    url(r'^document/(?P<pk>[0-9]+)/delete', document_delete, name='document_delete'),
    url(r'^statement_import/', StatementImportView.as_view(), name='statement_import'),
    url(r'^bot', include('django_telegrambot.urls')),
]
