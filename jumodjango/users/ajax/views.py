from datetime import datetime, timedelta
from django.http import HttpResponseBadRequest
from etc import cache
from etc.auth import login, logout, set_auth_cookies, unset_auth_cookies
from etc.decorators import PostOnly, AccountRequired
from etc.entities import create_handle
from etc.view_helpers import json_response, json_error
from etc.user import hash_password
from issue.models import Issue, UserToIssueFollow
import json
from message.models import Subscription, NOTIFICATIONS_PUB
from mailer.notification_tasks import send_notification, EmailTypes
from org.models import Org, UserToOrgFollow
from users.models import User, Location, UserToUserFollow, PasswordResetRequest
from uuid import uuid4


@AccountRequired
@PostOnly
def fbot_update(request):
    if 'ot' not in request.POST:
        return HttpResponseBadRequest()
    request.user.fb_access_token = request.POST['ot']
    request.user.save()
    cache.bust_on_handle(request.user, request.user.username)
    return json_response({})

@PostOnly
def fb_login(request):
    if 'id' not in request.POST or 'ot' not in request.POST:
        return HttpResponseBadRequest()
    user = User.objects.get(facebook_id = request.POST['id'], is_active=True)
    if user.fb_access_token != request.POST['ot']:
        user.fb_access_token = request.POST['ot']
        user.save()
    cache.put_on_handle(user, user.username)
    #perform for all that login magic that happens under the covers
    login(request, user)
    response = {'user_id':user.id, 'fb_access_token':user.fb_access_token}
    return set_auth_cookies(json_response({'result' : response}), user)

@PostOnly
def check_fbid(request):
    if 'fbid' not in request.POST:
        return HttpResponseBadRequest()
    fbid = request.POST['fbid']
    if not fbid:
        return json_response({'exists' : 0})
    try:
        u = User.objects.get(facebook_id = fbid, is_active=True)
        return json_response({'exists' : 1})
    except:
        pass
    return json_response({'exists' : 0})

@AccountRequired
@PostOnly
def update_user(request):
    if 'user' not in request.POST:
        return HttpResponseBadRequest()
    user = json.loads(request.POST['user'])

    if 'location' in user and user['location']:
        loc = user['location']
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
        request.user.location = _loc
    else:
        request.user.location = None

    str_fields = [
                    'first_name', 'last_name', 'email', 'gender', 'bio',
                    'url', 'twitter_id', 'flickr_id', 'youtube_id', 'vimeo_id', 'blog_url',
                 ]

    settings_fields = [
                    'enable_jumo_updates', 'email_stream_frequency', 'post_to_fb',
                  ]

    int_fields = [
                    'birth_year',
                 ]

    if 'enable_followed_notification' in user:
        try:
            sub = request.user.subscriptions.get(id=NOTIFICATIONS_PUB)
        except Subscription.DoesNotExist:
            sub = Subscription.get_or_create(user=request.user, pub_id=NOTIFICATIONS_PUB)

        if sub.subscribed <> user['enable_follow_notification']:
            sub.subscribed = user['enable_follow_notification']
            sub.save()

    for f in str_fields:
        if f in user and user[f] != getattr(request.user, f):
            setattr(request.user, f, user[f])

    for f in settings_fields:
        settings = user['settings']
        if f in settings:
            setattr(request.user, f, settings[f])

    for f in int_fields:
        if f in user and user[f] != getattr(request.user, f):
            if user[f] == '':
                user[f] = None
            setattr(request.user, f, user[f])

    if 'password' in user and user['password'] != '':
        request.user.password = hash_password(user['password'])
    if 'username' in user and user['username'] != request.user.username:
        _username = request.user.username
        request.user.username = create_handle(user['username'])
        cache.bust_on_handle(request.user, _username, False)

    request.user.save()
    cache.bust_on_handle(request.user, request.user.username)
    return json_response({'result' : request.user.username})

@AccountRequired
@PostOnly
def follow(request):
    action = request.POST['action']
    item_type = request.POST['item_type']

    if 'items[]' in request.POST:
        try:
            items = request.POST.getlist('items[]')
        except:
            items = [request.POST['items[]']]
    elif 'items' in request.POST:
        try:
            items = list(json.loads(request.POST['items']))
        except:
            items = [request.POST['items']]

    for item in items:
        ent = None
        item_id_type = 'id'

        if len(item) == 24:
            item_id_type = 'mongo_id'

        if item_type == 'org':
            try:
                if item_id_type == 'id':
                    ent = Org.objects.get(id = item)
                else:
                    ent = Org.objects.get(mongo_id = item)
                f, created = UserToOrgFollow.objects.get_or_create(user = request.user, org = ent)
                if action == 'follow':
                    f.following = True
                else:
                    f.following = False
                    f.stopped_following = datetime.now()
                f.save()
                request.user.refresh_orgs_following()

                ent.refresh_users_following()
                #if created:
                #    FeedStream.post_new_follow(request.user, ent)
            except Exception, inst:
                log(inst)

        elif item_type == 'issue':
            try:
                if item_id_type == 'id':
                    ent = Issue.objects.get(id = item)
                else:
                    ent = Issue.objects.get(mongo_id = item)
                f, created = UserToIssueFollow.objects.get_or_create(user = request.user, issue = ent)
                if action == 'follow':
                    f.following = True
                else:
                    f.following = False
                    f.stopped_following = datetime.now()
                f.save()
                request.user.refresh_issues_following()
                ent.refresh_users_following()
                #if created:
                #    FeedStream.post_new_follow(request.user, ent)

            except Exception, inst:
                log(inst)

        else:
            try:
                if item_id_type == 'id':
                    ent = User.objects.get(id = item)
                else:
                    ent = User.objects.get(mongo_id = item)
                f, created = UserToUserFollow.objects.get_or_create(follower = request.user, followed = ent)
                if action == 'follow':
                    f.is_following = True
                else:
                    f.is_following = False
                    f.stopped_following = datetime.now()
                f.save()
                request.user.refresh_users_following()
                ent.refresh_followers()
                if created:
                    #FeedStream.post_new_follow(request.user, ent)
                    send_notification(type=EmailTypes.FOLLOW,
                                      user=ent,
                                      entity=request.user)
            except Exception, inst:
                log(inst)

        if not ent:
            continue
        else:
            cache.bust(ent)

    return json_response({'result' : 1})

@AccountRequired
@PostOnly
def remove_user(request):
    request.user.is_active = False
    request.user.save()
    cache.bust_on_handle(request.user, request.user.username)
    logout(request)
    return unset_auth_cookies(json_response({'result':1}))

@PostOnly
def forgot_password(request):
    email = request.POST['email'].strip()
    try:
        u = User.objects.get(email = email, is_active=True)
    except:
        return json_error(INVALID_EMAIL_ERROR, 'No user at that email address.')
    pr = PasswordResetRequest()
    pr.user = u
    pr.uid = str(uuid4().hex)
    pr.save()
    p = PasswordResetRequest.objects.all()
    send_notification(type=EmailTypes.RESET_PASSWORD,
                                  user=u,
                                  entity=u,
                                  password_reset_id=pr.uid)
    return json_response({'response' : 1})

#NEED TO WALK THROUGH OLD POINTLESS VIEWS WITH BRENNAN
@PostOnly
def request_password(request):
    pass

@PostOnly
def reset_password(request):
    pass
