from datetime import date
from django.db import models
from django.utils.translation import ugettext as _
from djmoney.models.fields import MoneyField


class Account(models.Model):
    TYPES = (
        ('income', _('Income')),
        ('expense', _('Expense')),
        ('account', _('Account')),
    )

    title = models.CharField(
        verbose_name=_('Title'),
        max_length=255,
        blank=True)
    value = MoneyField(
        verbose_name=_('Value'),
        max_digits=50,
        decimal_places=5)
    type = models.CharField(
        verbose_name=_('Type'),
        choices=TYPES,
        max_length=8)

    interest_rate = models.DecimalField(
        verbose_name=_('Interest rate (%)'),
        max_digits=50,
        decimal_places=5,
        null=True,
        blank=True)
    interest_rate_day = models.DateField(
        verbose_name=_('Date of next interest rate accrual'),
        blank=True,
        null=True)
    interest_rate_is_monthly = models.BooleanField(
        verbose_name=_('Monthly'),
        help_text=_('Mark if interest rate is accrued monthly'),
        default=True
    )

    @property
    def expected_interest_rate(self):
        # TODO Get some more info about interest rates and their calculations
        if self.interest_rate:
            if self.interest_rate_is_monthly:
                return self.interest_rate / 100 * self.value / 12
            else:
                return self.interest_rate / 100 / 365 * (self.closed - self.opened).days * self.value
        else:
            return None

    opened = models.DateField(
        verbose_name=_('Date of open'),
        null=True, blank=True)
    closed = models.DateField(
        verbose_name=_('Date of close'),
        null=True, blank=True)

    credentials = models.TextField(
        verbose_name=_('Credentials'),
        blank=True
    )

    def __str__(self):
        return '{type} {title} ({value})'.format(
            type=self.type,
            title=self.title,
            value=self.value
        )

    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')

class Invoice(models.Model):
    date = models.DateField(
        verbose_name=_('Date'),
        auto_now_add=True,
        blank=True
    )

    def __str__(self):
        return _('Invoice from {date}').format(
            date=self.date
        )


class Transaction(models.Model):
    source = models.ForeignKey(
        verbose_name=_('Source'),
        to=Account,
        related_name='source')

    destination = models.ForeignKey(
        verbose_name=_('Destination'),
        to=Account,
        related_name='destination')

    source_value = MoneyField(
        verbose_name=_('Value in source currency'),
        max_digits=50,
        decimal_places=5,
    )

    destination_value = MoneyField(
        verbose_name=_('Value in destination currency'),
        max_digits=50,
        decimal_places=5,
    )

    invoice = models.ForeignKey(
        verbose_name=_('Invoice'),
        to=Invoice
    )

    def __str__(self):
        return '{date}: {source} → {destination}, {value}'.format(
            date=self.date,
            source=self.source.title,
            destination=self.destination.title,
            value=self.source_value,
        )


class Document(models.Model):
    description = models.CharField(
        verbose_name=_('Description'),
        max_length=1024,
        blank=True
    )

    invoice = models.ForeignKey(
        verbose_name=_('Invoice'),
        to=Invoice
    )

    file = models.FileField(
        verbose_name=_('File with image')
    )
