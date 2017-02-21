import logging

from django.db import models, transaction, connection
from django.db.models import Sum, F
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from djmoney.models.fields import CurrencyField
from treebeard.ns_tree import NS_Node


logger = logging.getLogger(__name__)


class Account(NS_Node):
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
    bank_title = models.CharField(
        verbose_name=_('title used by bank to identify account in messages anf reports'),
        max_length=255,
        blank=True,
    )

    type = models.IntegerField(
        verbose_name=_('type'),
        choices=TYPES)
    dashboard = models.BooleanField(
        verbose_name=_('display on dashboard'),
        default=False
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
        """
        Property contains list of sheaves for the account, sorted buy currency
        in alphabetical order. Sheaf in base currency will be placed of first
        place if exists.
        :return:
        """
        result = list()
        for sheaf in self.sheaves.order_by('currency'):
            if sheaf.currency == settings.BASE_CURRENCY:
                result.insert(0, sheaf)
            else:
                result.append(sheaf)
        return result

    def recalculate_summary(self, atomic=True):
        def do():
            self.sheaves.all().delete()
            result = Transaction.objects.filter(account=self)\
                .filter(approved=True)\
                .values('currency')\
                .annotate(amount=Sum('amount'))
            for item in result:
                Sheaf.objects.create(account=self,
                                     amount=item['amount'],
                                     currency=item['currency']).save()

        if atomic:
            with transaction.atomic():
                do()
        else:
            do()

    def summary_at(self, date):
        """
        method returns QuerySet with dictionaries with expected account summary
         for specified date (including that date) for this account and all
         child ones. Result is sorted by currency in alphabetical order.

        >>> account = Account.objects.get(pk=1)
        >>> account.summary_at(date.today())
        <QuerySet [{'currency': 'RUB', 'amount': Decimal('88891.50000')},
                   {'currency': 'USD', 'amount': Decimal('200.00000')}]>

        :param date: date of summary
        :return: dictionary with summary
        """
        return Transaction.objects.filter(account__in=self.get_tree(self))\
            .filter(date__lte=date)\
            .values('currency')\
            .annotate(amount=Sum('amount'))\
            .order_by('currency')

    def tree_summary(self):
        """
        method returns summary of all child accounts ordered by currency
        >>> account = Account.objects.get(pk=34)
        >>> account.tree_summary()
        <QuerySet [{'currency': 'GBP', 'amount': Decimal('99.00000')},
                   {'currency': 'RUB', 'amount': Decimal('89119.50000')},
                   {'currency': 'USD', 'amount': Decimal('281.00000')}]>

        :return: QuerySet with summary
        """
        return Sheaf.objects.filter(account__in=self.get_tree(self))\
            .values('currency')\
            .annotate(amount=Sum('amount')).order_by('currency')

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
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES
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

    def __eq__(self, other):
        return type(other) == Sheaf and \
               self.account == other.account and \
               self.amount == other.amount and \
               self.currency == other.currency

    def __ne__(self, other):
        return not self.__eq__(other)

    class Meta:
        unique_together = ('account', 'currency')


class Invoice(models.Model):
    timestamp = models.DateTimeField(
        verbose_name=_('date and time')
    )

    comment = models.TextField(
        verbose_name=_('comment'),
        blank=True
    )

    user = models.ForeignKey(
        verbose_name=_('user'),
        to=User,
        blank=True,
        null=True
    )

    def verify(self):
        """
        method calculates sum of all transactions of the invoice and returns
        QuerySet with currencies that has outstanding transactions.

        >>> invoice = Invoice.objects.get(pk=3)
        >>> invoice.verify()
        <QuerySet [{'amount': Decimal('70000.00000'), 'currency': 'RUB'}]>

        :return: QuerySet with amounts and currencies. Empty QuerySet can
         be thought as sign of verified invoice.
        """
        return Transaction.objects.filter(invoice=self)\
            .values('currency')\
            .annotate(amount=Sum('amount'))\
            .exclude(amount=0)

    @property
    def is_verified(self):
        return not bool(self.verify())

    def __str__(self):
        return _('Invoice from {timestamp}').format(
            timestamp=self.timestamp
        )


class Transaction(models.Model):
    date = models.DateField(
        verbose_name=_('date')
    )
    approved = models.BooleanField(
        verbose_name=_('approved'),
        default=True
    )

    account = models.ForeignKey(
        verbose_name=_('account'),
        to=Account,
        related_name='transactions'
    )

    amount = models.DecimalField(
        verbose_name=_('amount'),
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
    )

    currency = CurrencyField(
        verbose_name=_('currency'),
        default=settings.BASE_CURRENCY,
        price_field=amount
    )

    invoice = models.ForeignKey(
        to=Invoice,
        related_name='transactions',
        blank=True, null=True, default=None
    )

    comment = models.TextField(
        verbose_name=_('comment'),
        blank=True
    )

    def __str__(self):
        return ('{amount} {currency} @ {account} on {date} ({app}approved)'
                .format(amount=self.amount,
                        currency=self.currency,
                        account=self.account,
                        date=self.date,
                        app='not ' if not self.approved else ''))

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.id:
            sheaf = self.account.sheaves.filter(currency=self.currency).first()
            if not sheaf:
                Sheaf.objects.create(account=self.account,
                                     currency=self.currency,
                                     amount=self.amount).save()
            else:
                sheaf.amount += self.amount
                sheaf.save()
            super(Transaction, self).save(*args, **kwargs)
        else:
            old_account = Transaction.objects.get(pk=self.pk).account
            super(Transaction, self).save(*args, **kwargs)
            self.account.recalculate_summary(atomic=False)
            if self.account != old_account:
                old_account.recalculate_summary(atomic=False)


class Document(models.Model):
    description = models.CharField(
        verbose_name=_('description'),
        max_length=1024,
        blank=True
    )

    invoice = models.ForeignKey(
        verbose_name=_('invoice'),
        to=Invoice,
        related_name='documents'
    )

    file = models.FileField(
        verbose_name=_('file with image')
    )
