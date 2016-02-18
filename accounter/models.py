from datetime import date
from django.db import models


class AccountGroup(models.Model):
    title = models.CharField(max_length=255)
    parent = models.ForeignKey('AccountGroup', blank=True, null=True)

    def __str__(self):
        return self.title


class Account(models.Model):
    TYPES = (
        ('income', 'Income'),
        ('expense', 'Expence'),
        ('account', 'Account'),
    )

    title = models.CharField(max_length=255, blank=True)
    value = models.DecimalField(max_digits=50, decimal_places=5)
    interest_rate = models.DecimalField(max_digits=50, decimal_places=5, null=True, blank=True)
    interest_rate_day = models.IntegerField(blank=True, null=True)
    type = models.CharField(choices=TYPES, max_length=30)
    category = models.ForeignKey(AccountGroup)
    currency = models.CharField(default='RUB', max_length=3)
    opened = models.DateField(null=True, blank=True)
    closed = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class Transaction(models.Model):
    date = models.DateField(auto_now_add=True, null=True)
    parent = models.ForeignKey('Transaction', blank=True, null=True)
    source = models.ForeignKey(Account, related_name='source')
    destination = models.ForeignKey(Account, related_name='destination', blank=True, null=True)
    value = models.DecimalField(max_digits=50, decimal_places=5)
    currency = models.CharField(default='RUB', max_length=3)
    source_value = models.DecimalField(max_digits=50, decimal_places=5, blank=True)
    destination_value = models.DecimalField(max_digits=50, decimal_places=5, blank=True)

    def __str__(self):
        return '{date}: {source} → {destination}, {value} {currency}'.format(
            date=self.date,
            source=self.source,
            destination=self.destination,
            value=self.value,
            currency=self.currency
        )


class Invoice(models.Model):
    description = models.CharField(max_length=1024, blank=True)
    transaction = models.ForeignKey(Transaction)
    file = models.FileField()
    mime_type = models.CharField(max_length=255)

    def __str__(self):
        return 'Invoice for {transaction} ({description})'.format(
            transaction=self.transaction,
            description=self.description
        )
