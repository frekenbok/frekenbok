import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class StatementImportView(LoginRequiredMixin, TemplateView):
    template_name = 'accountant/statement_import.html'
