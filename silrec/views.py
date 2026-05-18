from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import View, TemplateView
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.db import transaction

from datetime import datetime, timedelta

from silrec.helpers import is_internal, has_access
from silrec.forms import *
from silrec.components.proposals.models import Proposal

from django.core.management import call_command
import json
from decimal import Decimal

import os
import zipfile
import io

import logging
logger = logging.getLogger('payment_checkout')

from django.contrib.auth import logout
from django.contrib.auth.views import LogoutView

class UserLogoutView(LogoutView):

    def get(self, request):
        logout(request)
        return redirect('/')


class InternalView(UserPassesTestMixin, TemplateView):
    template_name = 'silrec/dash/index.html'

    def test_func(self):
        return is_internal(self.request) and has_access(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return render(self.request, 'silrec/index.html')
        return self.no_permissions_fail(self.request)

    def get_context_data(self, **kwargs):
        context = super(InternalView, self).get_context_data(**kwargs)
        context['dev'] = settings.DEV_STATIC
        context['dev_url'] = settings.DEV_STATIC_URL
        return context

class ExternalView(LoginRequiredMixin, TemplateView):
    #template_name = 'sqs/dash/index.html'
    template_name = 'silrec/index.html'

    def get_context_data(self, **kwargs):
        context = super(ExternalView, self).get_context_data(**kwargs)
        context['dev'] = settings.DEV_STATIC
        context['dev_url'] = settings.DEV_STATIC_URL
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not has_access(request.user):
            return render(request, 'silrec/index.html')
        return super().dispatch(request, *args, **kwargs)


class SilrecRoutingView(TemplateView):
    template_name = 'silrec/index.html'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            if not self.request.user.is_staff:
                return super(SilrecRoutingView, self).get(*args, **kwargs)
            if not has_access(self.request.user):
                return super(SilrecRoutingView, self).get(*args, **kwargs)
            if is_internal(self.request):
                return redirect('internal')
            return redirect('external')
        kwargs['form'] = LoginForm
        return super(SilrecRoutingView, self).get(*args, **kwargs)
        #return redirect('/accounts/login')


class SilrecContactView(TemplateView):
    template_name = 'silrec/contact.html'


class SilrecFurtherInformationView(TemplateView):
    template_name = 'silrec/further_info.html'


class InternalProposalView(DetailView):
    model = Proposal
    #template_name = "silrec/dash/index.html"
    template_name = "silrec/index.html"

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            if not has_access(self.request.user):
                return super(SilrecRoutingView, self).get(*args, **kwargs)
            if is_internal(self.request):
                return super().get(*args, **kwargs)
            return redirect("external")
        kwargs["form"] = LoginForm
        return super(SilrecRoutingView, self).get(*args, **kwargs)

'''
FROM DAS!!!
class DisturbanceRoutingView(TemplateView):
    template_name = 'disturbance/index.html'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            if is_internal(self.request):
                return redirect('internal')
            return redirect('external')
        kwargs['form'] = LoginForm
        return super(DisturbanceRoutingView, self).get(*args, **kwargs)


class MasterlistContactView(TemplateView):
    template_name = 'sqs/contact.html'

class MasterlistFurtherInformationView(TemplateView):
    template_name = 'sqs/further_info.html'

@login_required(login_url='ds_home')
def first_time(request):
    context = {}
    if request.method == 'POST':
        form = FirstTimeForm(request.POST)
        redirect_url = form.data['redirect_url']
        if not redirect_url:
            redirect_url = '/'
        if form.is_valid():
            # set user attributes
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.dob = form.cleaned_data['dob']
            request.user.save()
            return redirect(redirect_url)
        context['form'] = form
        context['redirect_url'] = redirect_url
        return render(request, 'sqs/user_profile.html', context)
    # GET default
    if 'next' in request.GET:
        context['redirect_url'] = request.GET['next']
    else:
        context['redirect_url'] = '/'
    context['dev'] = settings.DEV_STATIC
    context['dev_url'] = settings.DEV_STATIC_URL
    #return render(request, 'sqs/user_profile.html', context)
    return render(request, 'sqs/dash/index.html', context)


class HelpView(LoginRequiredMixin, TemplateView):
    template_name = 'sqs/help.html'

    def get_context_data(self, **kwargs):
        context = super(HelpView, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated:
            application_type = kwargs.get('application_type', None)
            if kwargs.get('help_type', None)=='operator':
                if is_internal(self.request):
                    qs = HelpPage.objects.filter(application_type__name__icontains=application_type, help_type=HelpPage.HELP_TEXT_INTERNAL).order_by('-version')
                    context['help'] = qs.first()
#                else:
#                    return TemplateResponse(self.request, 'sqs/not-permitted.html', context)
#                    context['permitted'] = False
            else:
                qs = HelpPage.objects.filter(application_type__name__icontains=application_type, help_type=HelpPage.HELP_TEXT_EXTERNAL).order_by('-version')
                context['help'] = qs.first()
        return context
'''


class ManagementCommandsView(LoginRequiredMixin, TemplateView):
    template_name = 'forest_blocks/mgt-commands.html'

    def post(self, request):
        data = {}
        command_script = request.POST.get('script', None)
        if command_script:
            print ('running {}'.format(command_script))
            call_command(command_script)
            data.update({command_script: 'true'})

        return render(request, self.template_name, data)


class DbDumpListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """List and download db_dump files."""
    template_name = 'silrec/db_dumps.html'

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name__in=['Operator', 'Reviewer', 'Silrec Admin']).exists()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        dump_dir = os.path.join(settings.BASE_DIR, settings.DB_DUMPS_DIR)
        dumps = []
        if os.path.isdir(dump_dir):
            for f in os.listdir(dump_dir):
                fpath = os.path.join(dump_dir, f)
                if os.path.isfile(fpath) and f.endswith('.sql.zip'):
                    size = os.path.getsize(fpath)
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                    dumps.append({
                        'filename': f,
                        'size': _human_size_v(size),
                        'modified': mtime.strftime('%Y-%m-%d %H:%M:%S'),
                        'mtime': mtime,
                    })
            dumps.sort(key=lambda d: d['mtime'], reverse=True)
        ctx['dumps'] = dumps
        ctx['dump_dir_exists'] = os.path.isdir(dump_dir)
        ctx['db_dumps_dir'] = settings.DB_DUMPS_DIR
        ctx['is_superuser'] = self.request.user.is_superuser
        return ctx

    def post(self, request, *args, **kwargs):
        import threading
        def run_dump():
            from io import StringIO
            try:
                call_command('db_dump')
            except Exception:
                pass
        t = threading.Thread(target=run_dump, daemon=True)
        t.start()
        return JsonResponse({'success': True})


def _human_size_v(b):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if b < 1024:
            return f'{b:.1f} {unit}'
        b /= 1024
    return f'{b:.1f} TB'


class DbDumpDownloadView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Stream a dump file for download."""

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, filename):
        if '..' in filename or '/' in filename:
            raise Http404
        fpath = os.path.join(settings.BASE_DIR, settings.DB_DUMPS_DIR, filename)
        if not os.path.isfile(fpath):
            raise Http404
        with open(fpath, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response


class DbDumpDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Delete a db dump file. Only superuser."""

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, filename):
        if '..' in filename or '/' in filename:
            raise Http404
        dump_dir = os.path.join(settings.BASE_DIR, settings.DB_DUMPS_DIR)
        fpath = os.path.join(dump_dir, filename)
        if not os.path.isfile(fpath):
            raise Http404
        os.remove(fpath)
        return JsonResponse({'success': True})


class GeneratedReportListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """List and download generated report exports."""
    template_name = 'silrec/generated_reports.html'

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return self.request.user.groups.filter(name__in=['Operator', 'Reviewer', 'Silrec Admin']).exists()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        report_dir = os.path.join(settings.BASE_DIR, settings.REPORT_EXPORT_DIR)
        reports = []
        if os.path.isdir(report_dir):
            for f in os.listdir(report_dir):
                fpath = os.path.join(report_dir, f)
                if os.path.isfile(fpath) and not f.endswith('.meta'):
                    size = os.path.getsize(fpath)
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
                    user = ''
                    meta_path = os.path.join(report_dir, f'{f}.meta')
                    if os.path.isfile(meta_path):
                        with open(meta_path) as mf:
                            for line in mf:
                                if line.startswith('user='):
                                    user = line.split('=', 1)[1].strip()
                    reports.append({
                        'filename': f,
                        'size': _human_size_v(size),
                        'modified': mtime.strftime('%Y-%m-%d %H:%M:%S'),
                        'user': user,
                        'mtime': mtime,
                    })
            reports.sort(key=lambda r: r['mtime'], reverse=True)
        ctx['reports'] = reports
        ctx['report_dir_exists'] = os.path.isdir(report_dir)
        ctx['retention_days'] = settings.REPORT_RETENTION_DAYS
        ctx['report_export_dir'] = settings.REPORT_EXPORT_DIR
        ctx['is_silrec_admin'] = self.request.user.groups.filter(name='Silrec Admin').exists()
        return ctx


class GeneratedReportDownloadView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Stream a generated report file for download."""

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, filename):
        if '..' in filename or '/' in filename:
            raise Http404
        fpath = os.path.join(settings.BASE_DIR, settings.REPORT_EXPORT_DIR, filename)
        if not os.path.isfile(fpath):
            raise Http404
        with open(fpath, 'rb') as f:
            content = f.read()
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        content_types = {
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'pdf': 'application/pdf',
            'shz': 'application/octet-stream',
            'zip': 'application/zip',
        }
        ct = content_types.get(ext, 'application/octet-stream')
        response = HttpResponse(content, content_type=ct)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class GeneratedReportDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Delete a generated report file. Only Silrec Admin group."""

    def test_func(self):
        return self.request.user.groups.filter(name='Silrec Admin').exists()

    def post(self, request, filename):
        if '..' in filename or '/' in filename:
            raise Http404
        report_dir = os.path.join(settings.BASE_DIR, settings.REPORT_EXPORT_DIR)
        fpath = os.path.join(report_dir, filename)
        if not os.path.isfile(fpath):
            raise Http404
        os.remove(fpath)
        # Remove companion metadata file if it exists
        meta_path = os.path.join(report_dir, f'{filename}.meta')
        if os.path.isfile(meta_path):
            os.remove(meta_path)
        return JsonResponse({'success': True})
