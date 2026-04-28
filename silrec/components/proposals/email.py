import logging
from email.mime.text import MIMEText
import json
from datetime import datetime

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_str
#from django.core.urlresolvers import reverse
from django.urls import reverse
from django.conf import settings

from silrec.components.emails.emails import TemplateEmailBase
from silrec.components.proposals.models import ProposalLogEntry
#from ledger.accounts.models import EmailUser
from django.contrib.auth.models import User, Group
#from silrec.components.main.models import GlobalSettings

logger = logging.getLogger(__name__)

SYSTEM_NAME = settings.SYSTEM_NAME_SHORT + ' Automated Message'

#django.utils.encoding.smart_text = smart_str

def get_sender_user():
    sender = settings.DEFAULT_FROM_EMAIL
    try:
        sender_user = User.objects.get(email__icontains=sender)
    except:
        User.objects.create(email=sender, password='')
        sender_user = User.objects.get(email__icontains=sender)
    return sender_user

def get_assessor_recipients():
    try:
        emails = Group.objects.get(name='Assessor').user_set.all().values_list('email', flat=True)
    except Exception as e:
        raise Exception (f'{e}: No email recipients found for Assessor - possibly No Group called "Assessor" defined or assigned to user(s)')
    return list(emails)

def get_fmb_sharepoint_url():
    sharepoint_url = ''
    try:
        sharepoint_url = GlobalSettings.objects.get(key=GlobalSettings.FMB_SHAREPOINT_PAGE).value
    except:
        sharepoint_url = ''
    return sharepoint_url


#class ProposalApprovalSendNotificationEmail(TemplateEmailBase):
#    subject = 'Your Proposal has been approved.'
#    html_template = 'disturbance/emails/proposals/send_approval_notification.html'
#    txt_template = 'disturbance/emails/proposals/send_approval_notification.txt'


#class AmendmentRequestSendNotificationEmail(TemplateEmailBase):
#    subject = 'An amendment to your Proposal is required.'
#    html_template = 'disturbance/emails/proposals/send_amendment_notification.html'
#    txt_template = 'disturbance/emails/proposals/send_amendment_notification.txt'


class SubmitSendNotificationEmail(TemplateEmailBase):
    subject = 'A new Proposal has been submitted.'
    html_template = 'silrec/emails/proposals/send_submit_notification.html'
    #txt_template = 'silrec/emails/proposals/send_submit_notification.txt'
    txt_template = None


class ReviewerSendNotificationEmail(TemplateEmailBase):
    subject = 'Proposal has been updated for review.'
    html_template = 'silrec/emails/proposals/send_review_notification.html'
    txt_template = None


class ReviewCompletedSendNotificationEmail(TemplateEmailBase):
    subject = 'Proposal review have been completed.'
    html_template = 'silrec/emails/proposals/send_review_completed_notification.html'
    txt_template = None


class ReturnedSendNotificationEmail(TemplateEmailBase):
    subject = 'Proposal has been returned for further details.'
    html_template = 'silrec/emails/proposals/send_returned_notification.html'
    txt_template = None


def send_submit_email_notification(request, proposal):
    email = SubmitSendNotificationEmail()
    try:
        url = request.build_absolute_uri(reverse('internal-proposal-detail',kwargs={'proposal_pk': proposal.id}))
        if "-internal" not in url:
            # add it. This email is for internal staff (assessors)
            url = '-internal.{}'.format(settings.SITE_DOMAIN).join(url.split('.' + settings.SITE_DOMAIN))
    except Exception as e:
            # for testing, eg. send_submit_email_notification(request=None, proposal=p)
            url = f'{settings.SITE_URL}/internal/proposal/proposal.id'
    context = {
        'proposal': proposal,
        'url': url,
        'greeting': 'Assessor',
        'assessor_footer': True,
        'FMB': get_fmb_sharepoint_url(),
        'comment': proposal.latest_transition_comment or '',
    }

    #msg = email.send(proposal.assessor_recipients, context=context)
    #import ipdb; ipdb.set_trace()
    msg = email.send(get_assessor_recipients(), context=context)
    sender = get_sender_user()
    _log_proposal_email(msg, proposal, sender=sender)
    return msg

def send_reviewer_email_notification(request, proposal):
    email = ReviewerSendNotificationEmail()
    try:
        url = request.build_absolute_uri(reverse('internal-proposal-detail',kwargs={'proposal_pk': proposal.id}))
        if "-internal" not in url:
            # add it. This email is for internal staff (assessors)
            url = '-internal.{}'.format(settings.SITE_DOMAIN).join(url.split('.' + settings.SITE_DOMAIN))
    except Exception as e:
            # for testing, eg. send_submit_email_notification(request=None, proposal=p)
            url = f'{settings.SITE_URL}/internal/proposal/proposal.id'
    context = {
        'proposal': proposal,
        'url': url,
        'greeting': 'Reviewer',
        'reviewer_footer': True,
        'FMB': get_fmb_sharepoint_url(),
    }

    msg = email.send(get_assessor_recipients(), context=context)
    sender = get_sender_user()
    _log_proposal_email(msg, proposal, sender=sender)
    return msg

def send_review_completed_email_notification(request, proposal):
    email = ReviewCompletedSendNotificationEmail()
    try:
        url = request.build_absolute_uri(reverse('internal-proposal-detail',kwargs={'proposal_pk': proposal.id}))
        if "-internal" not in url:
            # add it. This email is for internal staff (assessors)
            url = '-internal.{}'.format(settings.SITE_DOMAIN).join(url.split('.' + settings.SITE_DOMAIN))
    except Exception as e:
            # for testing, eg. send_submit_email_notification(request=None, proposal=p)
            url = f'{settings.SITE_URL}/internal/proposal/proposal.id'
    context = {
        'proposal': proposal,
        'url': url,
        'greeting': 'Review Completed',
        'review_completed_footer': True,
        'FMB': get_fmb_sharepoint_url(),
    }

    msg = email.send(get_assessor_recipients(), context=context)
    sender = get_sender_user()
    _log_proposal_email(msg, proposal, sender=sender)
    return msg

def send_returned_email_notification(request, proposal):
    email = ReturnedSendNotificationEmail()
    try:
        url = request.build_absolute_uri(reverse('internal-proposal-detail',kwargs={'proposal_pk': proposal.id}))
        if "-internal" not in url:
            # add it. This email is for internal staff (assessors)
            url = '-internal.{}'.format(settings.SITE_DOMAIN).join(url.split('.' + settings.SITE_DOMAIN))
    except Exception as e:
            # for testing, eg. send_submit_email_notification(request=None, proposal=p)
            url = f'{settings.SITE_URL}/internal/proposal/proposal.id'
    context = {
        'proposal': proposal,
        'url': url,
        'greeting': 'Assessor',
        'assessor_footer': True,
        'FMB': get_fmb_sharepoint_url(),
        'comment': proposal.latest_transition_comment or '',
    }

    msg = email.send(get_assessor_recipients(), context=context)
    sender = get_sender_user()
    _log_proposal_email(msg, proposal, sender=sender)
    return msg

def _log_proposal_email(email_message, proposal, sender=None):
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_str(sender) if sender else smart_str(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_str(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_str(email_message)
        subject = ''
        to = proposal.submitter.email
        fromm = smart_str(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    #customer = proposal.submitter
    customer = proposal.submitter_obj

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'proposal': proposal,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = ProposalLogEntry.objects.create(**kwargs)

    return email_entry


#def _log_user_email(email_message, emailuser, customer ,sender=None):
#    from ledger.accounts.models import EmailUserLogEntry
#    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
#        # TODO this will log the plain text body, should we log the html instead
#        text = email_message.body
#        subject = email_message.subject
#        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
#        # the to email is normally a list
#        if isinstance(email_message.to, list):
#            to = ','.join(email_message.to)
#        else:
#            to = smart_text(email_message.to)
#        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
#        all_ccs = []
#        if email_message.cc:
#            all_ccs += list(email_message.cc)
#        if email_message.bcc:
#            all_ccs += list(email_message.bcc)
#        all_ccs = ','.join(all_ccs)
#
#    else:
#        text = smart_text(email_message)
#        subject = ''
#        to = customer
#        fromm = smart_text(sender) if sender else SYSTEM_NAME
#        all_ccs = ''
#
#    customer = customer
#
#    staff = sender
#
#    kwargs = {
#        'subject': subject,
#        'text': text,
#        'emailuser': emailuser,
#        'customer': customer,
#        'staff': staff,
#        'to': to,
#        'fromm': fromm,
#        'cc': all_ccs
#    }
#
#    email_entry = EmailUserLogEntry.objects.create(**kwargs)
#
#    return email_entry

