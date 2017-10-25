from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from os.path import join, dirname, realpath
from random import random

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from moneyed import RUB, USD, EUR

from accountant.models import Account, Sheaf, Invoice, Transaction, Document


def add_test_data(cls):
    # Test user
    cls.test_user_password = 'QQa8ZezCQr4doOSIB+p1bPJNP+ZxZVmrwgDMNOqZ'
    cls.test_user = User.objects.create_user(
        username='john_dow',
        email='j.dow@example.com',
        password=cls.test_user_password
    )

    # Test accounts
    cls.cash = Account(title='Наличные', type=Account.ACCOUNT, dashboard=True)
    Account.add_root(instance=cls.cash)

    cls.wallet = cls.cash.add_child(title='Кошелёк', type=Account.ACCOUNT)
    for currency in (RUB, EUR):
        Sheaf.objects.create(amount=int(random() * 100),
                             currency=currency,
                             account=cls.wallet)

    cls.reserve = cls.cash.add_child(title='Заначка', type=Account.ACCOUNT)

    cls.bank = Account(title='Банк', type=Account.ACCOUNT, dashboard=True)
    Account.add_root(instance=cls.bank)
    cls.card = cls.bank.add_child(
        title='Дебетовая карта',
        bank_title='Karta *1234',
        type=Account.ACCOUNT,
        credentials='Счёт: 1234567890987654321\nБИК: 0020045354023\nКИК: 235255'
    )

    # Opening balance
    opening_balance = Account(title='Входящий остаток',
                              type=Account.INCOME,
                              opened=date(2015, 3, 1),
                              closed=date(2015, 3, 1))
    cls.opening_balance = Account.add_root(instance=opening_balance)
    ob_invoice = Invoice.objects.create(
        timestamp=datetime.now(tz=timezone.utc),
        comment='Входящий остаток'
    )
    Transaction.objects.create(
        date=date(2015, 3, 1),
        account=cls.opening_balance,
        amount=Decimal('-134.5'),
        currency=RUB,
        invoice=ob_invoice
    )
    Transaction.objects.create(
        date=date(2015, 3, 1),
        account=cls.wallet,
        amount=Decimal('134.5'),
        currency=RUB,
        invoice=ob_invoice
    )
    Transaction.objects.create(
        date=date(2015, 3, 1),
        account=cls.opening_balance,
        amount=Decimal('-19000'),
        currency=RUB,
        invoice=ob_invoice
    )
    Transaction.objects.create(
        date=date(2015, 3, 1),
        account=cls.reserve,
        amount=Decimal('19000'),
        currency=RUB,
        invoice=ob_invoice
    )

    # Test income
    job = Account(title='Работа', type=Account.INCOME)
    Account.add_root(instance=job)
    cls.job = Account.objects.get(pk=job.pk)
    salary = cls.job.add_child(title='Зарплата', type=Account.INCOME)
    cls.salary = Account.objects.get(pk=salary.pk)
    cls.bonus = cls.job.add_child(title='Премия', type=Account.INCOME)

    # Test expenses
    cls.expenses = [
        Account(title=expense, type=Account.EXPENSE)
        for expense in ('Бензин', 'Хлеб', 'Колбаса')
    ]
    for expense in cls.expenses:
        Account.add_root(instance=expense)

    # Test income
    cls.first_salary = Invoice.objects.create(timestamp=datetime(2015, 4, 1, tzinfo=timezone.utc))
    cls.first_salary_income_tx = Transaction.objects.create(
        date=date(2015, 4, 1),
        account=cls.salary,
        amount=Decimal(-70000),
        currency=RUB,
        invoice=cls.first_salary,
    )
    cls.first_salary_internal_tx = Transaction.objects.create(
        date=date(2015, 4, 1),
        account=cls.wallet,
        amount=Decimal(70000),
        currency=RUB,
        invoice=cls.first_salary
    )

    cls.first_bonus = Invoice.objects.create(timestamp=datetime(2015, 4, 2, tzinfo=timezone.utc))
    Transaction.objects.create(
        date=date(2015, 4, 2),
        account=cls.bonus,
        amount=Decimal(-200),
        currency=USD,
        invoice=cls.first_bonus
    )
    Transaction.objects.create(
        date=date(2015, 4, 2),
        account=cls.wallet,
        amount=Decimal(200),
        currency=USD,
        invoice=cls.first_bonus
    )

    # Test expenses
    cls.first_invoice = Invoice.objects.create(timestamp=datetime(2015, 4, 3, tzinfo=timezone.utc))
    sum_of_first_invoice = Decimal(0)
    for expense in cls.expenses:
        value = int(random() * 100)
        sum_of_first_invoice += value
        Transaction.objects.create(
            date=date(2015, 4, 3),
            account=expense,
            amount=value,
            currency=RUB,
            invoice=cls.first_invoice
        )
    Transaction.objects.create(
        date=date(2015, 4, 3),
        account=cls.wallet,
        amount=-sum_of_first_invoice,
        currency=RUB,
        invoice=cls.first_invoice
    )

    cls.second_invoice = Invoice.objects.create(timestamp=datetime(2015, 4, 4, tzinfo=timezone.utc))
    value = int(random() * 100)
    Transaction.objects.create(
        date=date(2015, 4, 4),
        account=cls.wallet,
        amount=-value,
        currency=RUB,
        invoice=cls.second_invoice,
        comment='салями'
    )
    Transaction.objects.create(
        date=date(2015, 4, 4),
        account=cls.expenses[-1],
        amount=value,
        currency=RUB,
        invoice=cls.second_invoice,
        comment='салями'
    )

    cls.third_invoice = Invoice.objects.create(timestamp=datetime(2015, 4, 5, tzinfo=timezone.utc))
    value = int(random() * 100)
    Transaction.objects.create(
        date=date(2015, 4, 5),
        account=cls.wallet,
        amount=-value,
        currency=RUB,
        invoice=cls.third_invoice,
        comment='АИ-95'
    )
    cls.third_invoice_expense_tx = Transaction.objects.create(
        date=date(2015, 4, 5),
        account=cls.expenses[0],
        amount=value,
        currency=RUB,
        invoice=cls.third_invoice,
        comment='АИ-95'
    )

    cls.internal_transfer_invoice = Invoice.objects.create(
        comment='Transfer between accounts',
        timestamp=datetime(2015, 8, 5, tzinfo=timezone.utc)
    )
    value = int(random() * 100)
    Transaction.objects.create(
        date=date(2015, 8, 5),
        account=cls.wallet,
        amount=-value,
        currency=RUB,
        invoice=cls.internal_transfer_invoice
    )
    Transaction.objects.create(
        date=date(2015, 8, 5),
        account=cls.reserve,
        amount=value,
        currency=RUB,
        invoice=cls.internal_transfer_invoice
    )

    cls.disbalanced_invoice = Invoice.objects.create(
        comment='Invoice with broken balance',
        timestamp=datetime.now(tz=timezone.utc)
    )
    Transaction.objects.create(
        date=date.today(),
        account=cls.reserve,
        amount=int(random() * 100),
        currency=RUB,
        invoice=cls.disbalanced_invoice
    )

    test_pdf = read_file('test_invoice_document.pdf')
    test_img = read_file('test_invoice_image.jpg')

    cls.invoice_with_attached_image = Invoice.objects.create(
        comment='Invoice with attached image',
        timestamp=datetime.now(tz=timezone.utc)
    )
    cls.document_as_pdf = Document.objects.create(
        description='Some PDF as document',
        invoice=cls.invoice_with_attached_image,
        file=SimpleUploadedFile('test_doc.pdf', test_pdf, 'application/pdf')
    )
    cls.document_as_img = Document.objects.create(
        description='Some image as document',
        invoice=cls.invoice_with_attached_image,
        file=SimpleUploadedFile('test_image.jpg', test_img, 'image/jpeg')
    )
    cls.document_without_invoice = Document.objects.create(
        description='Some document without invoice',
        invoice=None,
        file=SimpleUploadedFile('test_image.jpg', test_img, 'image/jpeg')
    )

    # Test futures transaction
    cls.future = Transaction.objects.create(
        date=date.today() + timedelta(days=10),
        account=cls.wallet,
        amount=Decimal('200'),
        currency=RUB,
        comment='Future transaction'
    )


def read_file(filename: str, mode='rb'):
    with open(join(dirname(realpath(__file__)), filename), mode) as f:
        result = f.read()
    return result
