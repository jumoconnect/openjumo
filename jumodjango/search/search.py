from users.models import User
from org.models import Org
from issue.models import Issue
import pysolr
import settings

class Search:
    @classmethod
    def search(cls, term, limit=20, restrict_type = None):
        results = []
        params = {'defType': 'dismax',
                  'rows': limit,
                  'start': 0,
                  'qf': 'name locations keywords^0.8',
                  'bf': 'social_score'}

        if restrict_type and restrict_type != 'all_orgtypes':
            params['qf'] = list(params['qf'])
            params['qf'].append('id:%s*' % restrict_type)

        solr = pysolr.Solr(settings.SOLR_CONN)
        results = solr.search(term, **params)

        return results