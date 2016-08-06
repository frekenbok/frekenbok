from django.db import models
from django.utils.translation import ugettext as _
from django.conf import settings
from djmoney.models.fields import MoneyField, CurrencyField
from moneyed import Money, CURRENCIES


MAX_DIGITS = 50
DECIMAL_PLACES = 5


class Account(models.Model):
    INCOME = 1
    EXPENSE = 2
    ACCOUNT = 3
    TYPES = (
        (INCOME, _('income')),
        (EXPENSE, _('expense')),
        (ACCOUNT, _('account')),
    )

    title = models.CharField(
        verbose_name=_('title'),
        max_length=255,
        blank=True)

    type = models.IntegerField(
        verbose_name=_('type'),
        choices=TYPES)
    parent = models.ForeignKey(
        verbose_name=_('parent account'),
        to='Account',
        related_name='children',
        blank=True, null=True
    )

    opened = models.DateField(
        verbose_name=_('date of open'),
        null=True, blank=True, auto_now_add=True
    )
    closed = models.DateField(
        verbose_name=_('date of close'),
        null=True, blank=True
    )

    credentials = models.TextField(
        verbose_name=_('credentials'),
        blank=True
    )

    @property
    def sorted_sheaves(self):
        result = list()
        for sheaf in self.sheaves.order_by('currency'):
            if sheaf.currency == settings.BASE_CURRENCY:
                result.insert(0, sheaf)
            else:
                result.append(sheaf)
        return result

    def __str__(self):
        return '{title} ({type})'.format(
            title=self.title,
            type=dict(self.TYPES)[self.type]
        )

    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')


class Sheaf(models.Model):
    account = models.ForeignKey(
        verbose_name=_('account'),
        to=Account,
        related_name='sheaves'
    )
    amount = models.DecimalField(
        verbose_name=_('sheaf'),
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES
    )
    currency = CurrencyField(
        verbose_name=_('currency'),
        price_field='amount',
        default=settings.BASE_CURRENCY
    )

    def __str__(self):
        return '{amount} {currency} on {account}'.format(
            amount=self.amount,
            currency=self.currency,
            account=self.account
        )


class Invoice(models.Model):
    date = models.DateField(
        verbose_name=_('date')
    )

    def __str__(self):
        return _('Invoice from {date}').format(
            date=self.date
        )


class Transaction(models.Model):
    source = models.ForeignKey(
        verbose_name=_('source'),
        to=Account,
        related_name='source')

    destination = models.ForeignKey(
        verbose_name=_('destination'),
        to=Account,
        related_name='destination')

    source_value = MoneyField(
        verbose_name=_('value in source currency'),
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
    )

    destination_value = MoneyField(
        verbose_name=_('value in destination currency'),
        max_digits=MAX_DIGITS,
        decimal_places=DECIMAL_PLACES,
    )

    invoice = models.ForeignKey(
        verbose_name=_('invoice'),
        to=Invoice
    )

    def __str__(self):
        return '{date}: {source} → {destination}, {value}'.format(
            date=self.invoice.date,
            source=self.source.title,
            destination=self.destination.title,
            value=self.source_value,
        )


class Document(models.Model):
    description = models.CharField(
        verbose_name=_('description'),
        max_length=1024,
        blank=True
    )

    invoice = models.ForeignKey(
        verbose_name=_('invoice'),
        to=Invoice
    )

    file = models.FileField(
        verbose_name=_('file with image')
    )
