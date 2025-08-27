import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from leaseslicensing.components.proposals.models import Proposal
from leaseslicensing.components.proposals.utils import test_proposal_emails


class PreviewLicencePDFView(View):
    def post(self, request, *args, **kwargs):
        response = HttpResponse(content_type="application/pdf")

        proposal = self.get_object()
        details = json.loads(request.POST.get("formData"))

        response.write(proposal.preview_approval(request, details))
        return response

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs["proposal_pk"])


class TestEmailView(View):
    def get(self, request, *args, **kwargs):
        test_proposal_emails(request)
        return HttpResponse("Test Email Script Completed")
