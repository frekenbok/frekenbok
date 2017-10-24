import logging

from django.apps import apps
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse, HttpResponseBadRequest
from django.views.generic import TemplateView

from accountant.models import Document

logger = logging.getLogger(__name__)


class StatementImportView(LoginRequiredMixin, TemplateView):
    template_name = 'accountant/statement_import.html'

    def post(self, request: HttpRequest, *args, **kwargs):
        statement = request.FILES.get('statement')
        if statement:
            doc = Document.objects.create(
                file=statement,
                invoice=None,
                description=""
            )
            return JsonResponse(doc.json())

        try:
            document_id = int(request.POST.get('document'))
        except ValueError:
            return HttpResponseBadRequest(
                'Can\'t parse {} as document id'.format(
                    request.POST.get('document')))

        settings.INSTALLED_APPS

        apps