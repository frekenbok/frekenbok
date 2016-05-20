from django.db import models
from django.utils.translation import ugettext as _
from django.conf import settings
from djmoney.models.fields import MoneyField, CurrencyField
from moneyed import Money, CURRENCIES


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
    amount = MoneyField(
        verbose_name=_('amount'),
        max_digits=50,
        decimal_places=5)
    currency = CurrencyField(
        verbose_name=_('currency'),
        price_field=amount,
        default=settings.BASE_CURRENCY
    )

    interest_rate = models.DecimalField(
        verbose_name=_('interest rate (%)'),
        max_digits=50,
        decimal_places=5,
        null=True,
        blank=True)
    interest_rate_day = models.DateField(
        verbose_name=_('date of next interest rate accrual'),
        blank=True,
        null=True)
    interest_rate_is_monthly = models.BooleanField(
        verbose_name=_('monthly'),
        help_text=_('Mark if interest rate is accrued monthly.'),
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
        verbose_name=_('date of open'),
        null=True, blank=True)
    closed = models.DateField(
        verbose_name=_('date of close'),
        null=True, blank=True)

    credentials = models.TextField(
        verbose_name=_('credentials'),
        blank=True
    )

    def __str__(self):
        return '{title} ({value})'.format(
            title=self.title,
            value=self.value
        )

    def get_by_currency(self, currency):
        if currency not in CURRENCIES:
            raise ValueError('{} is not valid currency'.format(currency))
        else:
            return se

    class Meta:
        verbose_name = _('account')
        verbose_name_plural = _('accounts')


class Invoice(models.Model):
    date = models.DateField(
        verbose_name=_('date'),
        auto_now_add=True,
        blank=True
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
        max_digits=50,
        decimal_places=5,
    )

    destination_value = MoneyField(
        verbose_name=_('value in destination currency'),
        max_digits=50,
        decimal_places=5,
    )

    invoice = models.ForeignKey(
        verbose_name=_('invoice'),
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
