from django_jenkins.management.commands import jenkins
try:
    import cProfile as profile
except ImportError:
    import profile
import pstats

class Command(jenkins.Command):
    def handle(self, *test_labels, **options):
        profile.runctx('super(Command, self).handle(*test_labels, **options)',
                       {},
                       {'Command': Command, 'self': self, 'test_labels': test_labels, 'options': options},
                       'reports/jenkins.profile',
                       )
        p = pstats.Stats('reports/jenkins.profile')
        p.strip_dirs().sort_stats('cumulative')
        p.print_stats()
