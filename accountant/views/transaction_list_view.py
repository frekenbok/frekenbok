import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from accountant.models import Transaction

logger = logging.getLogger(__name__)


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    context_object_name = 'transaction'