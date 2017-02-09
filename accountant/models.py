from django.db import models, transaction, connection
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from djmoney.models.fields import CurrencyField
from treebeard.ns_tree import NS_Node


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

    type = models.IntegerField(
        verbose_name=_('type'),
        choices=TYPES)

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
            sql = 'SELECT SUM(`amount`) as amount, `currency` ' \
                  'FROM accountant_transaction ' \
                  'WHERE `account_id` = %s AND `approved` ' \
                  'GROUP BY `currency`;'
            with connection.cursor() as cursor:
                cursor.execute(sql, (self.id, ))
                result = cursor.fetchall()
            for amount, currency in result:
                Sheaf.objects.create(account=self,
                                     amount=amount,
                                     currency=currency).save()

        if atomic:
            with transaction.atomic():
                do()
        else:
            do()

    def summary_at(self, date):
        """
        method returns dictionary with expected account summary
         for specified date (including that date)
        :param date: date of summary
        :return: dictionary with summary
        """
        sql = 'SELECT SUM(`amount`) as amount, `currency`' \
              'FROM accountant_transaction ' \
              'WHERE `account_id` IN (' \
              '   SELECT `id`' \
              '   FROM accountant_account' \
              '   WHERE `lft` > %s AND `rgt` < %s AND `tree_id` = %s' \
              ') AND date <= %s ' \
              'GROUP BY `currency` ORDER BY `currency`;'
        with connection.cursor() as cursor:
            cursor.execute(sql, (self.lft, self.rgt, self.tree_id))
            result = cursor.fetchall()
        return {currency: amount for amount, currency in result}

    def tree_summary(self):
        """
        method returns summary of all child accounts
        >>> account = Account.objects.get(pk=34)
        >>> account.tree_summary()
        {'EUR': Decimal('34'),
         'RUB': Decimal('45')}
        :return: dict with summary
        """
        sql = 'SELECT SUM(`amount`) as amount, `currency`' \
              'FROM accountant_sheaf ' \
              'WHERE `account_id` IN (' \
              '   SELECT `id`' \
              '   FROM accountant_account' \
              '   WHERE `lft` > %s AND `rgt` < %s AND `tree_id` = %s' \
              ') GROUP BY `currency` ORDER BY `currency`;'
        with connection.cursor() as cursor:
            cursor.execute(sql, (self.lft, self.rgt, self.tree_id))
            result = cursor.fetchall()
        return {currency: amount for amount, currency in result}

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
        dictionary with currencies that has outstanding transactions.
        >>> invoice = Invoice.objects.get(pk=3)
        >>> invoice.verify()
        {'EUR': Decimal('-34')}
        :return: dictionary with currencies as keys and outstanding amounts
          as values. Empty dictionary can be thought as sign of verified
          invoice.
        """
        sql = 'SELECT SUM(`amount`) as amount, `currency` FROM `{}` ' \
              'WHERE `invoice_id` = %s GROUP BY `currency`;'
        with connection.cursor() as cursor:
            cursor.execute(sql.format(Transaction._meta.db_table), [self.id])
            result = cursor.fetchall()
        return {currency: amount for amount, currency in result if amount}

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
