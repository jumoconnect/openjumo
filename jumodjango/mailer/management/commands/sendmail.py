from django.conf import settings
from django.core.management.base import BaseCommand
import logging
from mailer.models import Email
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
            make_option('--send',
                action='store_true',
                dest='send',
                default=False,
                help='Send emails or just show a log of pending emails (defaults to latter).'),
            )

    def handle(self, *args, **options):
        if not options['send']:
            if settings.DEBUG:
                msgs = Email.objects.filter(sent = False).filter(recipient__icontains = '@jumo.com')
            else:
                msgs =[]
                #msgs = Email.objects.filter(sent = False)
            if not msgs:
                logging.info('No emails to send.')
                return
            for msg in msgs:
                logging.info('Emailing %s: %s' % (msg.recipient, msg.subject))
        else:
            pass
            #This isn't referencing anything...
            #send_mail()
