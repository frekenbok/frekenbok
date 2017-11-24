import logging
import mimetypes
import os

from decimal import Decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Sum, Func
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from djmoney.models.fields import CurrencyField
from treebeard.ns_tree import NS_Node

logger = logging.getLogger(__name__)


class Round(Func):
    function = 'ROUND'
    template='%(function)s(%(expressions)s, {})'.format(settings.DECIMAL_PLACES)


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

    def get_absolute_url(self):
        return reverse('accountant:account_detail', kwargs={'pk': self.pk})

    @property
    def depth_dashes(self):
        """
        That's a sort of dirty hack, returns string with several m-dashes.
        Number of dashes is equal to depth level of account in tree.
        :return: string with dashes
        """
        return '— ' * (self.depth - 1)

    @property
    def depth_nbsp(self):
        """
        That's a sort of dirty hack, returns string with several non-broken
        spaces. Number of spaces is equal to depth level of account in tree.
        :return: string with dashes
        """
        return '\u00A0' * (self.depth - 1)

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
                .annotate(amount=Sum('amount'))\
                .order_by('currency')
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

    @staticmethod
    def get_expenses():
        return Account.objects.filter(type=Account.EXPENSE).all()

    @staticmethod
    def get_accounts():
        return Account.objects.filter(type=Account.ACCOUNT).all()

    @staticmethod
    def get_incomes():
        return Account.objects.filter(type=Account.INCOME).all()

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

    def json(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'comment': self.comment,
            'user': self.user.id
        }

    def get_absolute_url(self):
        return reverse('accountant:invoice_detail', kwargs={'pk': self.pk})

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
        return self.transactions\
            .values('currency')\
            .annotate(amount=Round(Sum('amount')))\
            .exclude(amount=Decimal('0'))\
            .order_by()

    @property
    def is_verified(self):
        return not bool(self.verify())

    @property
    def pnl(self):
        """
        Property contains grouped by currency sum of all transaction of this
         invoice applied to accounts with type Account.ACCOUNT. It's designed
         to give a point of the invoice: was it some income, some expense
         or just some transfer between own accounts.
        :return: QuerySet with amounts and currencies
        
        >>> invoice = Invoice.objects.get(pk=4)
        >>> invoice.verify()
        <QuerySet [{'amount': Decimal('-500.00000'), 'currency': 'RUB'}]>
        """
        return Transaction.objects\
            .filter(invoice=self)\
            .filter(account__type=Account.ACCOUNT)\
            .values('currency')\
            .annotate(amount=Sum('amount'))\
            .exclude(amount=0)\
            .order_by('currency')

    def __get_distinct_accounts_by_type(self, type: int):
        return Account.objects \
            .filter(transactions__invoice=self) \
            .filter(type=type) \
            .distinct()

    @property
    def incomes(self):
        """
        List of Account.INCOME accounts involved to this invoice
        """
        return self.__get_distinct_accounts_by_type(Account.INCOME)

    @property
    def expenses(self):
        """
        List of Account.EXPENSE accounts involved to this invoice
        """
        return self.__get_distinct_accounts_by_type(Account.EXPENSE)

    @property
    def accounts(self):
        """
        List of Account.ACCOUNT accounts involved to this invoice
        """
        return self.__get_distinct_accounts_by_type(Account.ACCOUNT)

    @property
    def income_transactions(self):
        return self.transactions.filter(account__in=self.incomes)

    @property
    def expense_transactions(self):
        return self.transactions.filter(account__in=self.expenses)

    @property
    def internal_transactions(self):
        return self.transactions.filter(account__in=self.accounts)

    def __str__(self):
        return _('Invoice dated by {timestamp}{comment}').format(
            timestamp=self.timestamp,
            comment=' ({})'.format(self.comment) if self.comment else ''
        )

    class Meta:
        ordering = ['-timestamp']


class Transaction(models.Model):
    UNITS = (
        ('pcs', _('pieces')),
        ('kg', _('kilos')),
        ('g', _('grams')),
        ('l', _('liters')),
        ('gal', _('gallons')),
        ('p', _('pounds'))
    )

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

    quantity = models.DecimalField(
        verbose_name=_('good quantity'),
        max_digits=settings.MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        null=True,
        blank=True,
        default=None
    )
    unit = models.CharField(
        verbose_name=_('unit of measurement'),
        max_length=255,
        choices=UNITS,
        null=True,
        blank=True,
        default=None
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

    @property
    def price(self):
        if self.quantity:
            return self.amount / self.quantity

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

    class Meta:
        ordering = ['-date']


class Document(models.Model):
    description = models.CharField(
        verbose_name=_('description'),
        max_length=1024,
        blank=True
    )

    invoice = models.ForeignKey(
        verbose_name=_('invoice'),
        to=Invoice,
        null=True,
        related_name='documents'
    )

    file = models.FileField(
        verbose_name=_('file with image'),
        upload_to='documents/%Y/%m/',
    )

    @property
    def mime_type(self):
        return mimetypes.guess_type(self.file.name)[0]

    @property
    def file_name(self):
        return os.path.basename(self.file.name)

    def json(self):
        return {
            'id': self.id,
            'description': self.description,
            'invoice': self.invoice.id if self.invoice else None,
            'file': self.file.url
        }