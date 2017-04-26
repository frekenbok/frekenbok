from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Account, Sheaf, Transaction, Document, Invoice


class AccountAdmin(TreeAdmin):
    form = movenodeform_factory(Account)

admin.site.register(Account, AccountAdmin)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'comment', 'amount', 'currency', 'date', 'approved')

admin.site.register(Transaction, TransactionAdmin)


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 2


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'comment', 'verify')
    inlines = (TransactionInline, DocumentInline)

admin.site.register(Invoice, InvoiceAdmin)


admin.site.register(Sheaf)
admin.site.register(Document)
