from django.contrib import admin

from .models import Account, Sheaf, Transaction, Document, Invoice

admin.site.register(Account)
admin.site.register(Sheaf)
admin.site.register(Transaction)
admin.site.register(Document)
admin.site.register(Invoice)
