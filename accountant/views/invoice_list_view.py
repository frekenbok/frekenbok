import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from accountant.models import Invoice

logger = logging.getLogger(__name__)


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    context_object_name = 'invoice_list'
    template_name = 'accountant/invoice_list.html'
    paginate_by = 20