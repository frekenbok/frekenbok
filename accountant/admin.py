from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import Account, Sheaf, Transaction, Document, Invoice


class AccountAdmin(TreeAdmin):
    form = movenodeform_factory(Account)


admin.site.register(Account, AccountAdmin)
admin.site.register(Sheaf)
admin.site.register(Transaction)
admin.site.register(Document)
admin.site.register(Invoice)
