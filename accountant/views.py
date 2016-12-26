from datetime import date

from decimal import Decimal
from django.db.models import F
from django.db.models import Q
from django.views.generic import ListView, DetailView
from django.views.generic.base import ContextMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings

from .models import Account, Transaction


class AccountantViewMixin(LoginRequiredMixin, ContextMixin):
    raise_exception = True

    def get_context_data(self, **kwargs):
        result = super(AccountantViewMixin, self).get_context_data(**kwargs)
        result['accountant_app'] = True
        return result


class DashboardView(ListView, AccountantViewMixin):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/dashboard.html'

    def get_queryset(self):
        '''
        Dashboard displays all accounts with Account.ACCOUNT type and without
        child accounts. Child free items in nested set can be found by
        :return:
        '''
        return self.model.objects\
            .filter(type=Account.ACCOUNT, lft__exact=F('rgt') - 1)\
            .filter(Q(closed__gte=date.today()) | Q(closed=None))

    def get_context_data(self, **kwargs):
        context = super(DashboardView, self).get_context_data(**kwargs)

        total = dict()
        for account in context['account_list']:
            for sheaf in account.sheaves.all():
                total.setdefault(sheaf.currency, Decimal('0'))
                total[sheaf.currency] += sheaf.amount

        # Generating report about total value of all accounts and
        # placing value in base currency to first place in that report
        report = list()
        for currency, amount in sorted(total.items(), key=lambda x: x[0]):
            report_line = {'currency': currency, 'amount': amount}
            if currency == settings.BASE_CURRENCY:
                report.insert(0, report_line)
            else:
                report.append(report_line)

        context['total'] = report
        context['menu_dashboard'] = True
        return context


class AccountListView(ListView, AccountantViewMixin):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/account_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.ACCOUNT) \
            .filter(Q(closed__gte=date.today()) | Q(closed=None))


class IncomeListView(ListView, AccountantViewMixin):
    model = Account
    context_object_name = 'income_list'
    template_name = 'accountant/income_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.INCOME) \
            .filter(Q(closed__gte=date.today()) | Q(closed=None))


class AccountDetailView(DetailView, AccountantViewMixin):
    model = Account
    context_object_name = 'account'
    template_name = 'accountant/account_detail.html'

    def get_context_data(self, **kwargs):
        context = super(AccountDetailView, self).get_context_data(**kwargs)
        if context['account'].type == Account.ACCOUNT:
            context['account_list'] = \
                self.model.objects.filter(type=Account.ACCOUNT)\
                    .filter(Q(closed__gte=date.today()) | Q(closed=None)).all()
        context['transaction_list'] = \
            Transaction.objects.filter(account=self.object)\
                .order_by('-date')[:10]
        return context


class TransactionListView(ListView):
    model = Transaction
    context_object_name = 'transaction'
