import datetime
from django.core.cache import cache as djcache
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str
from etc import cache
from etc.entities import create_handle
from etc.decorators import PostOnly, AccountRequired
from etc.view_helpers import json_response, json_error
from issue.models import Issue
import json
import logging
from etc.view_helpers import json_encode
from mailer.notification_tasks import send_notification, EmailTypes
from org.models import Org, UserToOrgFollow, OrgIssueRelationship
from users.models import Location
#from utils.donations import nfg_api
from utils.regex_tools import facebook_id_magic
from uuid import uuid4

@PostOnly
def fetch_org_by_centroid(request):
    try:
        lat = float(request.POST.get('lat'))
        lon = float(request.POST.get('lon'))
        limit = float(request.POST.get('limit', 20))
    except AttributeError:
        json_error(INVALID_CENTROID_ERROR)

    orgs = Org.objects.filter(location__latitude__range = (lat - limit, lat + limit)).filter(location__longitude__range = (lon - limit, lon + limit))[0:limit]
    return json_response(json_encode(orgs))


@PostOnly
def update_org(request):
    try:
        org = json.loads(request.POST.get('org', {}))
        org_id = int(org['id'])
    except AttributeError:
        json_error(INVALID_ORG_ID_ERROR)

    str_fields = [
                    'name', 'email', 'phone_number', 'url', 'img_url',
                    'revenue', 'size', 'vision_statement', 'mission_statement',
                    'blog_url', 'twitter_id', 'flickr_id', 'vimeo_id', 'youtube_id',
                 ]

    int_fields = [
                    'year_founded', 'facebook_id', # changed 'year' to 'year_founded' here -b
                 ]

    bool_fields = [
                    'fb_fetch_enabled', 'twitter_fetch_enabled',
                  ]

    original = Org.objects.get(id = org_id)


    if 'parent_orgs' in org:
        if org['parent_orgs']:
            original.parent_org = Org.objects.get(id = org['parent_orgs'][0])

    if 'ein' in org and org['ein'] != original.ein:
        original.donation_enabled = False
        if org['ein'] == '':
            original.ein = ''
        else:
            original.ein = org['ein']
            try:
                original.donation_enable = False
              #  if nfg_api.npo_is_donation_enabled(org['ein']):
              #      original.donation_enabled = True
            except Exception, inst:
                logging.exception("Error checking donation status with nfs")


    if 'child_orgs' in org:
        org['child_orgs'] = [int(o) for o in org['child_orgs']]
        for o in org['child_orgs']:
            if o not in [l.id for l in original.parentorg.all()]:
                original.parentorg.add(Org.objects.get(id = o))
        for o in original.parentorg.all():
            if o.id not in org['child_orgs']:
                original.parentorg.remove(Org.objects.get(id = o.id))

    # this probably needs to change down the road because i can't imagine this is very sustainable.
    for i in org['tags']['context']:
        iss = Issue.objects.get(name__iexact = i['name'])

        try:
            r = OrgIssueRelationship.objects.get(issue = iss, org = original)
            r.rank = i['tag_rank']
            r.date_updated = datetime.datetime.now()
            r.save()
        except:
            r = OrgIssueRelationship()
            r.issue = iss
            r.org = original
            r.date_created = datetime.datetime.now()
            r.date_updated = datetime.datetime.now()
            r.rank = i['tag_rank']
            r.save()

    '''
    {u'locality': u'New York', u'region': u'Brooklyn', u'longitude': u'-73.948883', u'country_name': u'United States', u'postal_code': u'', u'address': u'', u'latitude': u'40.655071', u'type': u'County', u'raw_geodata': {u'lang': u'en-US', u'popRank': u'0', u'name': u'Brooklyn', u'woeid': u'12589335', u'uri': u'http://where.yahooapis.com/v1/place/12589335', u'admin1': {u'content': u'New York', u'code': u'US-NY', u'type': u'State'}, u'admin3': None, u'admin2': {u'content': u'Brooklyn', u'code': u'', u'type': u'County'}, u'centroid': {u'latitude': u'40.655071', u'longitude': u'-73.948883'}, u'locality1': {u'content': u'New York', u'type': u'Town'}, u'locality2': None, u'country': {u'content': u'United States', u'code': u'US', u'type': u'Country'}, u'boundingBox': {u'northEast': {u'latitude': u'40.739471', u'longitude': u'-73.833359'}, u'southWest': {u'latitude': u'40.570679', u'longitude': u'-74.042068'}}, u'areaRank': u'5', u'postal': None, u'placeTypeName': {u'content': u'County', u'code': u'9'}}}
    '''

    if 'location' in org and org['location']:
        loc = org['location']
        raw_geodata = json.dumps(loc["raw_geodata"]) if isinstance(loc.get("raw_geodata"), dict) else loc.get("raw_geodata")
        #Until we fix duplicate locations we have to do the following...lame.
        _locs = Location.objects.filter(raw_geodata = raw_geodata,
            longitude = loc.get('longitude', None),
            latitude = loc.get('latitude', None),
            address = loc.get('address', ' '),
            region = loc.get('region', ' '),
            locality = loc.get('locality', ' '),
            postal_code = loc.get('postal_code', ' '),
            country_name = loc.get('country_name', ' '))

        if len(_locs) > 0:
            _loc = _locs[0]
        else:
            _loc = Location(raw_geodata = raw_geodata,
                longitude = loc.get('longitude', None),
                latitude = loc.get('latitude', None),
                address = loc.get('address', ' '),
                region = loc.get('region', ' '),
                locality = loc.get('locality', ' '),
                postal_code = loc.get('postal_code', ' '),
                country_name = loc.get('country_name', ' '),)
            _loc.save()
        original.location = _loc
    else:
        original.location = None

    if 'working_locations' in org:
        for loc in org['working_locations']:
            raw_geodata = json.dumps(loc["raw_geodata"]) if isinstance(loc.get("raw_geodata"), dict) else loc.get("raw_geodata")
            if raw_geodata not in [l.raw_geodata for l in original.working_locations.all()]:
                locs = Location.objects.filter(raw_geodata = raw_geodata,
                        longitude = loc.get('longitude', None),
                        latitude = loc.get('latitude', None),
                        address = loc.get('address', ' '),
                        region = loc.get('region', ' '),
                        locality = loc.get('locality', ' '),
                        postal_code = loc.get('postal_code', ' '),
                        country_name = loc.get('country_name', ' '),
                        )

                if len(locs) > 0:
                    new_l = locs[0]
                else:
                    new_l = Location(raw_geodata = raw_geodata,
                        longitude = loc.get('longitude', None),
                        latitude = loc.get('latitude', None),
                        address = loc.get('address', ' '),
                        region = loc.get('region', ' '),
                        locality = loc.get('locality', ' '),
                        postal_code = loc.get('postal_code', ' '),
                        country_name = loc.get('country_name', ' '),
                        )
                    new_l.save()


                #Until we clean up the location DB we can't use get.
                """
                new_l, created = Location.objects.get_or_create(
                        raw_geodata = json.dumps(loc["raw_geodata"]) if isinstance(loc.get("raw_geodata"), dict) else loc.get("raw_geodata"),
                        longitude = loc.get('longitude', None),
                        latitude = loc.get('latitude', None),
                        address = loc.get('address', ' '),
                        region = loc.get('region', ' '),
                        locality = loc.get('locality', ' '),
                        postal_code = loc.get('postal_code', ' '),
                        country_name = loc.get('country_name', ' '),
                        )
                """
                original.working_locations.add(new_l)
                original.save()

        raw_geos = []
        for new_loc in org['working_locations']:
            raw_geodata = json.dumps(new_loc["raw_geodata"]) if isinstance(new_loc.get("raw_geodata"), dict) else new_loc.get("raw_geodata")
            raw_geos.append(raw_geodata)

        for old_loc in original.working_locations.all():
            if old_loc.raw_geodata not in raw_geos:
                original.working_locations.remove(old_loc)



    for issue in original.issues.all():
        if issue.name.lower() not in [l['name'].lower() for l in org['tags']['context']]:
            r = OrgIssueRelationship.objects.get(issue = issue, org = original)
            r.delete()

    for f in str_fields:
        if f in org and org[f] != getattr(original, f):
            setattr(original, f, smart_str(org[f], encoding='utf-8'))

    for f in int_fields:
        if f in org and org[f] != getattr(original, f):
            if org[f]:
                setattr(original, f, int(org[f]))
            else:
                setattr(original, f, None)

    for f in bool_fields:
        if f in org and org[f] != getattr(original, f):
            setattr(original, f, org[f])

    if 'handle' in org and org['handle'] != original.handle:
        _handle = original.handle
        original.handle = create_handle(org['handle'])
        cache.bust_on_handle(original, _handle, False)

    if 'methods' in org:
        for method in org['methods']:
            if method not in [l.method for l in original.method_set.all()]:
                m = Method()
                m.method = method
                m.date_created = datetime.datetime.now()
                m.date_updated = datetime.datetime.now()
                m.org = original
                m.save()

        for method in original.method_set.all():
            if method.method not in org['methods']:
                method.delete()

    if 'accomplishments' in org:
        for acc in org['accomplishments']:
            if acc['text'] not in [l.description for l in original.accomplishment_set.all()]:
                a = Accomplishment()
                a.org = original
                a.header = acc.get('year', '')
                a.description = acc.get('text', '')
                a.save()

        for acc in original.accomplishment_set.all():
            acc_header = acc.header
            acc_description = acc.description
            delete = True
            for new_acc in org["accomplishments"]:
                if new_acc["year"] == acc_header and new_acc["text"] == acc_description:
                    delete = False
            if delete:
                acc.delete()

    original.save()
    try:
        cache.bust_on_handle(original, original.handle)
    except:
        pass
    return json_response({'result' : original.handle})


@PostOnly
def remove_org(request):
    try:
        id = getattr(request.POST, 'id')
        org = Org.objects.get(id = id)
    except AttributeError, ObjectDoesNotExist:
        return json_error(INVALID_ORG_ID_ERROR)

    # TODO: so, uh, we need to figure out if the current user is authorized to do this?

    org.delete()
    cache.bust_on_handle(org, org.handle, False)
    return json_response({'result' : 1})


@PostOnly
def flag_org(request):
    try:
        org_id = getattr(request.POST, 'org_id')
        org = Org.objects.get(id = org_id)
    except AttributeError, ObjectDoesNotExist:
        return json_error(CANNOT_FLAG_ERROR)

    # TODO: so, uh, we need to figure out if the current user is authorized to do this?
    org.flagged = True
    org.save()
    cache.bust_on_handle(org, org.handle, False)
    return json_response({'result' : True})

@PostOnly
@AccountRequired
def org_create(request):
    o = Org()
    o.name = request.POST['name'].encode('utf-8')
    o.handle = create_handle(request.POST['name'])
    o.vision_statement = request.POST['vision_statement'].encode('utf-8')
    if request.POST['social_mission'] == 'yes':
        o.social_mission = True
    else:
        o.social_mission = False
    if request.POST['profit'] == 'yes':
        o.profit_seeking = True
    else:
        o.profit_seeking = False

    o.save()
    if request.POST['admin'] == 'yes':
        o.admins.add(request.user)
        o.save()

    f, created = UserToOrgFollow.objects.get_or_create(user = request.user, org = o)
    f.following = True
    f.save()
    request.user.refresh_orgs_following()
    return json_response(json_encode(o))

#brennan added this one
@PostOnly
def normalize_facebook_id(request):
    facebook_id = request.POST['fbid']

    if facebook_id:
        try:
            facebook_id = facebook_id_magic(facebook_id)
        except:
            return json_error(123, 'Sorry, your Facebook ID is invalid')

    return json_response({"facebook_id": facebook_id })
