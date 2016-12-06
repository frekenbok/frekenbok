from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Account, Sheaf, Transaction, Document, Invoice


class AccountAdmin(TreeAdmin):
    form = movenodeform_factory(Account)

admin.site.register(Account, AccountAdmin)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'amount', 'currency', 'date')

admin.site.register(Transaction, TransactionAdmin)


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 2


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'comment', 'is_verified')
    inlines = (TransactionInline,)

admin.site.register(Invoice, InvoiceAdmin)


admin.site.register(Sheaf)
admin.site.register(Document)
