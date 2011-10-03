from django.http import HttpResponse
from etc.view_helpers import json_response
from etc.templatetags.tags import _create_static_url

import settings
import urllib
import urllib2
import json
from indexes import Autocomplete
from etc.view_helpers import render, render_string, json_response
from miner.web.ip_lookup import ip_to_lat_lon

DEFAULT_LIMIT = 20

def _get_orgs_near_me(request, query, lat=None, lon=None, distance=40, limit=3):
    orgs_near_me = []
    if not (lat and lon):
        location = ip_to_lat_lon(request.META.get('HTTP_X_FORWARDED_FOR'))
        lat, lon = location.get('latitude'), location.get('longitude')

    if lat and lon:
        # New York = 40.7834345, -73.9662495
        orgs_near_me = Autocomplete.near_me(query, lat, lon, distance, limit)

    return orgs_near_me

def _get_related_searches(query):
    if not query:
        return []

    try:        
        resp = urllib2.urlopen(settings.DATAMINE_BASE + '/related_searches?%s' % urllib.urlencode(dict(q=query)), timeout=2).read()
    
        result = json.loads(resp).get('result', [])
    except Exception, e:
        print 'EXCEPTION', e
        return []

    good_results = []
    for res, prob in result:
        if res.lower() != query.lower():
            good_results.append(res)
    return good_results
            
def ajax_search(request):
    search_results = []
    query = request.GET.get('q', None)

    selected_facet = request.GET.get('type', None)
    try:
        limit = int(request.GET.get('limit', DEFAULT_LIMIT))
    except ValueError:
        limit = DEFAULT_LIMIT

    try:
        offset = int(request.GET.get('offset', 0))
    except ValueError:
        offset = 0

    search_results = Autocomplete.search(query, restrict_type=selected_facet, limit=limit, offset=offset,
                                         restrict_location = request.GET.get('location', None))

    lat, lon = request.GET.get('lat', None), request.GET.get('lng', None)
    orgs_near_me = _get_orgs_near_me(request, query, lat, lon)
    more_results = (search_results.hits - int(offset)) > limit
    related_searches = _get_related_searches(query)

    if 'format' in request.GET and request.GET['format']=='html':
        ret = {'items': render_string(request, 'search/search_items.html', {'search_results' : search_results, 'query': query}),
               'facets': render_string(request, 'search/facets.html', {'search_results': search_results, 'selected_facet': selected_facet, 'query': query}),
               'related': render_string(request, 'search/related_searches.html', {'related_searches': related_searches}),
               'more_results': render_string(request, 'search/more_results.html', {'more_results': more_results})
               }

        if orgs_near_me:
            ret['nearMe'] = render_string(request, 'search/near_me.html', {'orgs_near_me': orgs_near_me})

        return json_response(ret)

def search_page(request):
    search_results = []
    orgs_near_me = []
    query = request.GET.get('q',None)
    search_results = Autocomplete.search(query)
    orgs_near_me = _get_orgs_near_me(request, query)
    more_results = search_results.hits > DEFAULT_LIMIT    
    related_searches = _get_related_searches(query)

    more_results = search_results.hits > DEFAULT_LIMIT

    title = "for %s" % query if query else ''

    return render(request, 'search/base.html', {
            'search_results' : search_results,
            'more_results': more_results,
            'query': query,
            'orgs_near_me': orgs_near_me,
            'related_searches': related_searches,
            'title' : "Search %s" % title
            })


def ajax_term_complete(request):
    """Term prefix autocomplete, Google-style, completes the phrase"""
    results = {}
    term = request.GET.get('q', None)
    results = Autocomplete.autocomplete(term)
    return json_response(results)

def autocomplete(request):
    """Legacy autocomplete, still used in the top search bar around the site"""
    def _format_search_result(res, idx):
        type, id = res.id.split(':')
        image_url = res.image_url
        if image_url and not image_url.startswith('http'):
            image_url=_create_static_url(image_url)

        return {'id' : id, 'index': idx, 'name' : res.name[0], 'type' : type, 'url' : res.url,
                'image_url' : image_url, 'num_followers' : res.popularity}

    results = Autocomplete.search(request.GET['search'])
    return json_response([_format_search_result(t, idx) for idx, t in enumerate(results)])
