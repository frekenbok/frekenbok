import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView

from accountant.misc import fns_parser
from accountant.models import Document, Account

logger = logging.getLogger(__name__)


class StatementImportView(LoginRequiredMixin, TemplateView):
    template_name = 'accountant/statement_import.html'

    @transaction.atomic
    def post(self, request: HttpRequest, *args, **kwargs):
        statement = request.FILES.get('statement')
        if statement:
            doc = Document.objects.create(
                file=statement,
                invoice=None,
                description=""
            )

            default_expense = getattr(settings, 'DEFAULT_EXPENSE', 10)
            default_account = getattr(settings, 'DEFAULT_ACCOUNT', 2)

            invoice = fns_parser.parse(
                doc.file.read().decode(),
                request.user,
                Account.objects.get(pk=default_expense),
                Account.objects.get(pk=default_account)
            )
            doc.invoice = invoice
            doc.save()

            result = invoice.json()
            result['url'] = reverse('accountant:invoice_edit',
                                    kwargs={'pk': invoice.pk})
            return JsonResponse(result)
