from bebop import *
from django.db import models
import copy
import cPickle as pickle
from config import solr

@SearchIndex('autocomplete', config=config.DismaxSolrConfig)
class Autocomplete(object):
    id = model.StrField('id', document_id=True)
    type = model.StrField('type')
    exact_name = model.StrField('exact_name')
    name = model.TitleField('name', multi_valued=True)
    geo_location = model.GeoPointField('geo_location', stored=False)
    stored_issues = model.StrField('stored_issues', multi_valued=True, indexed=False)
    locations = model.TitleField('locations', multi_valued=True)
    is_vetted = model.BooleanField('is_vetted')
    location_classifiers = model.StrField('location_classifiers', stored=False, multi_valued=True)

    # Followers for now, used mainly for boosting
    popularity = model.IntegerField('popularity')
    # Stored not indexed, for display
    summary = model.StrField('summary', indexed=False)
    # Indexed but not stored, stick content and any other
    # words we want to search on in here
    keywords = model.TextField('keywords', stored=False)

    url = model.StrField('url', indexed=False, stored=True)
    image_url = model.StrField('image_url', indexed=False, stored=True)

    @property
    def get_name(self):
        return self.exact_name

    @property
    def get_url(self):
        return self.url

    @property
    def get_image_small(self):
        return self.image_url

    @property
    def get_all_issues(self):
        return [pickle.loads(str(issue)) for issue in self.stored_issues if issue]

    @classmethod
    def from_model(cls, entity):
        # TODO: declarative way to do this in bebop
        model_type = entity.__class__.__name__
        primary_location = None
        location_classes = set()
        for location in entity.search_all_locations:
            if location:
                if location.classification:
                    location_classes.add(location.classification)

                if not primary_location and location.latitude and location.longitude:
                    primary_location = location

        index = Autocomplete(id = ':'.join([model_type, str(entity.id)]),
                            type = model_type,
                            exact_name = entity.search_exact_name,
                            name = entity.search_all_names,
                            is_vetted = entity.search_jumo_vetted,
                            locations = [unicode(loc) for loc in entity.search_all_locations],
                            popularity = entity.search_popularity,
                            summary = getattr(entity, 'summary', None),
                            keywords = entity.search_keywords,
                            url = entity.get_url,
                            image_url = entity.get_image_small,
                            )
        if location_classes:
            index.location_classifiers = location_classes

        if hasattr(entity, 'search_all_issues'):
            index.stored_issues = [pickle.dumps(issue) for issue in entity.search_all_issues]

        if primary_location:
            index.geo_location = ','.join([str(primary_location.latitude), str(primary_location.longitude)])

        return index

    @classmethod
    def base_params(cls):
        return solr.search(Autocomplete)\
            .dismax_of(Autocomplete.name, Autocomplete.locations, Autocomplete.keywords**0.8)\
            .boost(func.log(Autocomplete.popularity)).default_query('*:*')\
            .boost(Autocomplete.is_vetted**5)\
            .phrase_boost(Autocomplete.name, Autocomplete.locations, Autocomplete.keywords**0.8)\
            
    @classmethod
    def autocomplete(cls, term, limit=10):
        term = term.rsplit(' ', 1)
        if len(term) > 1:
            term, prefix = term
        else:
            term, prefix = None, term[0]
        
        q = Autocomplete.base_params().limit(limit)
        if term:
            q = q.query(term)
            
        # @TODO: try to find a better way to do prefix faceting, these puppies are case sensitive
        prefix = prefix.lower()
        q.facet_prefix(Autocomplete.name, prefix)
        
        res = q.execute()
        return [' '.join([term, completion]) if term else completion for completion in res.facet_fields[Autocomplete.name]]

    @classmethod
    def near_me(cls, term, latitude, longitude, distance, limit = 5):
        q = Autocomplete.base_params().query(term).limit(limit).filter(or_(Autocomplete.type=='Org', Autocomplete.type=='Issue'))

        # TODO: bebop support for all this
        q.params['d'] = distance
        q.params['sfield'] = Autocomplete.geo_location
        q.params['pt'] = ','.join([str(latitude), str(longitude)])

        q.filter('{!geofilt}')
        q.boost('recip(geodist(),2,200,20)')

        return q.execute()

    @classmethod
    def search(cls, term, limit=20, offset=0, with_facets=True, restrict_type = None, restrict_location = None):
        q = Autocomplete.base_params().limit(limit).offset(offset)
        if term:
            q.query(term)
        else:
            q.filter(or_(Autocomplete.type=='Org', Autocomplete.type=='Issue'))

        do_exclusions = restrict_type and restrict_type != 'All Results'

        if with_facets:
            q.facet(Autocomplete.type, method='enum')
            if do_exclusions:
                # TODO: add tag exclusions to bebop's faceting
                tag = 'selected'
                q.filter((Autocomplete.type==restrict_type).tag(tag))
                q.params['facet.field'] = LuceneQuery(Autocomplete.type)
                q.params['facet.field'].local_params.add('ex', tag)
                q.params['facet.field'] = unicode(q.params['facet.field'])[:-1]

        if restrict_location and restrict_location != 'All':
            q.filter(Autocomplete.location_classifiers==restrict_location)

        results = q.execute()
        # Slight hack, TODO: implement facet exclusions in bebop
        if do_exclusions:
            results.all_results=sum(results.facet_fields['type'].values())
        else:
            results.all_results=results.hits
        return results