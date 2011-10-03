from django.core.management.base import BaseCommand
from mailer.mgr import jumo_reader
from optparse import make_option


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
            make_option('--send',
                action='store_true',
                dest='send',
                default=False,
                help='Send emails or just show a log of pending emails (defaults to latter).'),
            make_option('-n',
                action='store',
                dest='num_users',
                default=None,
                help='Number of users to query'),
            )

    def handle(self, *args, **options):
        if not options.get('send'):
            pass
        else:
            jumo_reader(options.get('num_users'))
