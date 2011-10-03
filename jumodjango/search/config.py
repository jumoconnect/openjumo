import bebop
import settings
from jumodjango import search

solr = bebop.Solr()
solr.add_connection(settings.SOLR_CONN)
solr.autodiscover_indexes(search)
