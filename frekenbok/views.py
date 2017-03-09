from datetime import timedelta, date

from decimal import Decimal
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.views.generic import ListView

from accountant.models import Account


class DashboardView(LoginRequiredMixin, ListView):
    raise_exception = True

    model = Account
    context_object_name = 'account_list'
    template_name = 'dashboard.html'

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
        total_report = list()
        for currency, amount in sorted(total.items(), key=lambda x: x[0]):
            report_line = {'currency': currency, 'amount': amount}
            if currency == settings.BASE_CURRENCY:
                total_report.insert(0, report_line)
            else:
                total_report.append(report_line)

        today = date.today()
        overview_dates = [today - timedelta(days=i) for i in range(28, -1, -1)]
        overview = list()
        for account in self.model.objects.filter(type=Account.ACCOUNT, dashboard=True):
            report = account.tree_summary()
            item = {
                'account': account.title,
                'report': report,
                'weight': sum(i['amount'] for i in report),
                # TODO We should try to guess currency here
                'weight_currency': settings.BASE_CURRENCY,
                'historical': []
            }
            for summary in [account.summary_at(i) for i in overview_dates]:
                for i in summary:
                    if i['currency'] == settings.BASE_CURRENCY:
                        item['historical'].append(i['amount'])
            overview.append(item)

        context['overview'] = overview
        context['total'] = total_report
        context['menu_dashboard'] = True
        return context
