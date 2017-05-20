import logging
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import DetailView

from accountant.models import Account, Transaction

logger = logging.getLogger(__name__)


class AccountDetailView(LoginRequiredMixin, DetailView):
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