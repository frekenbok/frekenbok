from django.contrib import admin

from .models import Account, AccountGroup, Transaction, Invoice

admin.site.register(Account)
admin.site.register(AccountGroup)
admin.site.register(Transaction)
admin.site.register(Invoice)
