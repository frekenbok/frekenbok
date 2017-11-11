import logging
from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.views.generic import DetailView

from accountant.models import Account, Transaction

logger = logging.getLogger(__name__)


class AccountDetailView(LoginRequiredMixin, DetailView):
    model = Account
    context_object_name = 'account'
    template_name = 'accountant/account_detail.html'

    def get_context_data(self, **kwargs):
        today = date.today()
        start_of_month = today.replace(day=1)
        prev_month_end = start_of_month - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        context = super(AccountDetailView, self).get_context_data(**kwargs)
        context['transaction_list'] = \
            Transaction.objects.filter(account=self.object)\
                .order_by('-date')[:10]

        context['total_quantity'] = \
            Transaction.objects.filter(account=self.object)\
                .values('unit')\
                .annotate(quantity=Sum('quantity'))\
                .filter(quantity__isnull=False)\
                .order_by('quantity')

        context['this_month'] = \
            Transaction.objects.filter(account=self.object) \
                .filter(approved=True, date__gte=start_of_month) \
                .values('currency') \
                .annotate(amount=Sum('amount')) \
                .order_by('currency')

        context['prev_month'] = \
            Transaction.objects.filter(account=self.object) \
                .filter(approved=True) \
                .filter(date__gte=prev_month_start, date__lt=start_of_month) \
                .values('currency') \
                .annotate(amount=Sum('amount')) \
                .order_by('currency')

        context['start_of_month'] = start_of_month
        context['prev_month_start'] = prev_month_start
        context['prev_month_end'] = prev_month_end

        return context
