import logging
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView

from accountant.models import Account

logger = logging.getLogger(__name__)


class AccountListView(LoginRequiredMixin, ListView):
    model = Account
    context_object_name = 'account_list'
    template_name = 'accountant/account_list.html'

    def get_queryset(self):
        return self.model.objects.filter(type=Account.ACCOUNT) \
            .filter(Q(closed__gte=date.today()) | Q(closed=None))