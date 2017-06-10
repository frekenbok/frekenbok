import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView

from accountant.models import Invoice

logger = logging.getLogger(__name__)


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    context_object_name = 'invoice'
    template_name = 'accountant/invoice_detail.html'