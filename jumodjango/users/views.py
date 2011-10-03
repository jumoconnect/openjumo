import datetime
from datetime import timedelta
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect, HttpResponse, Http404
from etc import cache
from etc.entities import create_handle
from etc.auth import attempt_login, logout, set_auth_cookies, unset_auth_cookies
from etc.decorators import NotLoggedInRequired, AccountRequired, PostOnly
from etc.user import hash_password
from etc.view_helpers import render, json_response, render_inclusiontag, render_string
from lib.image_upload import upload_user_image
import logging
from mailer.notification_tasks import send_notification, EmailTypes
from message.models import Subscription, NOTIFICATIONS_PUB
from popularity.models import Section, Sections, TopList
from users.forms import LoginForm, CreateAccountForm, UserSettingsForm, PhotoUploadForm, UserNotificationsForm, UserConnectForm
from users.models import User, PasswordResetRequest, UserToUserFollow
from entity_items.models.location import Location
from utils import fb_helpers
from uuid import uuid4
import json
from discovery.models import DiscoveryMap
from django.shortcuts import get_object_or_404, redirect

@AccountRequired
def upload_photo(request):
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            u = form.save(commit=False)
            u.upload_profile_pic(form.cleaned_data['profile_pic'])
            u.save()
            return HttpResponseRedirect("/")
    else:
        form = PhotoUploadForm(instance=request.user)

    return render(request, 'user/photo_upload.html', {
            'user_photo_upload_form': form,
            'entity':request.user,
            'form': form,
    })

@NotLoggedInRequired
def login_permalink(request):
    form = LoginForm()
    post_auth_action = request.GET.get('post_auth_action', 'redirect');
    redirect_to = request.GET.get('redirect_to', None)
    redirect_to = redirect_to if redirect_to != "/login" else None
    if request.POST:
        form = LoginForm(request.POST)
        if form.is_valid():
            email_or_username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            redirect_to = form.cleaned_data['redirect_to']
            post_auth_action = form.cleaned_data['post_auth_action']

            if redirect_to == None or redirect_to == 'None':
                redirect_to = "/"

            user = attempt_login(request, email_or_username, password)
            if user is not None and user.is_active:
                response = HttpResponseRedirect(redirect_to)
                if post_auth_action == 'close':
                    response = render(request, 'util/closing_window.html')

                return set_auth_cookies(response, user)
            else:
                form._errors["username"] = form.error_class(['The username and password you entered are incorrect.'])

    return render(request, 'user/login.html', {
        'title' : 'Login',
        'redirect_to' : redirect_to,
        'post_auth_action' : post_auth_action,
        'login_form': form})

def logout_permalink(request):
    logout(request)
    return unset_auth_cookies(HttpResponseRedirect(reverse('index')))

@NotLoggedInRequired
def setup(request):
    sans_facebook = True if request.GET.has_key('sans_facebook') and request.GET['sans_facebook'] else False
    redirect_to = request.GET.get('redirect_to', "/")

    form = CreateAccountForm(initial={'redirect_to': redirect_to,})
    if request.POST:
        sans_facebook = True if request.POST.has_key('sans_facebook') and request.POST['sans_facebook'] else False
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            u = User()
            u.bio = form.cleaned_data['bio']
            u.birth_year = form.cleaned_data['birth_year']
            u.email = u.long_email = form.cleaned_data['email']
            u.fb_access_token = form.cleaned_data['fb_access_token']
            u.gender = form.cleaned_data['gender']
            u.first_name = form.cleaned_data['first_name']
            u.last_name = form.cleaned_data['last_name']
            u.facebook_id = form.cleaned_data['fbid']
            u.bio = u.bio.encode('utf-8') if u.bio else ""
            u.first_name = u.first_name.encode('utf-8') if u.first_name else ""
            u.last_name = u.last_name.encode('utf-8') if u.last_name else ""
            if form.cleaned_data['location_data']:
                u.location = Location.get_or_create(form.cleaned_data['location_data'])
            u.next_email_time = datetime.datetime.now() + timedelta(days = 1)
            u.username = create_handle('%s%s' % (u.first_name, u.last_name))
            u.password = hash_password(form.cleaned_data['password'])
            u.save()

            Subscription.get_or_create(user = u, pub_id = NOTIFICATIONS_PUB)

            #Post to Facebook
            if form.cleaned_data['post_to_facebook']:
                fb_helpers.post_joined_to_wall(u)

            cache.put_on_handle(u, u.username)

            redirect_to = form.cleaned_data['redirect_to'] or '/'
            #perform for all that login magic that happens under the covers
            attempt_login(request, u.username, form.cleaned_data["password"])
            return set_auth_cookies(HttpResponseRedirect(redirect_to), u)

    return render(request, 'user/setup.html', {
        'title' : 'Setup your account',
        'create_form' : form,
        'sans_facebook': sans_facebook,
        })

@AccountRequired
def discover(request):
    return render(request, 'user/discover.html', {
        'title' : 'Discover'
        })

@AccountRequired
def home(request):
    top_categories, sub_category_groups, discovery_item_groups = DiscoveryMap.get_lists()
    list_ids = [l.id for l in Section.get_lists(Sections.SIGNED_IN_HOME)]
    lists = TopList.get_entities_for_lists(list_ids)
    if len(lists) > 0:
        recommended_orgs = lists.items()[0][1]
    else:
        recommended_orgs = []


    form = PhotoUploadForm(instance=request.user)

    return render(request, 'user/home.html', {
            'user_photo_upload_form': form,
            'title' : 'Home',
            'entity' : None,
            'top_categories': top_categories,
            'sub_category_groups': sub_category_groups,
            'discovery_item_groups': discovery_item_groups,
            'recommended_orgs': recommended_orgs
    })

@AccountRequired
def settings(request):
    success = False
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, request.FILES, instance=request.user)

        old_pw_hash = request.user.password
        if form.is_valid():
            u = form.save(commit=False)
            if u.password:
                u.password = hash_password(u.password)
            else:
                u.password = old_pw_hash
            if form.cleaned_data['profile_pic']:
                u.upload_profile_pic(form.cleaned_data['profile_pic'])
            if form.cleaned_data['location_data']:
                u.location = Location.get_or_create(form.cleaned_data['location_data'])
            u.save()
            success = True
    else:
        if request.user.location:
            location_input = str(request.user.location)
            location_data = request.user.location.to_json()
        else:
            location_input = location_data = ''
        form = UserSettingsForm(instance=request.user, initial={'location_input':location_input,
                                                                'location_data':location_data,})

    return render(request, 'user/settings.html', {
            'success': success,  #to drop a little notice like "CONGRATS #WINNING"
            'entity':request.user,
            'form': form,
    })

@AccountRequired
def notifications(request):
    success = False
    if request.POST:
        form = UserNotificationsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            success = True
    else:
        form = UserNotificationsForm(instance=request.user)

    return render(request, 'user/notifications.html', {
        'form': form,
        'success': success,  #to drop a little notice like "CONGRATS #WINNING"
    })

@AccountRequired
def connect(request):
    success = False
    if request.POST:
        form = UserConnectForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            success = True
    else:
        form = UserConnectForm(instance=request.user)

    return render(request, 'user/connect.html', {
        'form': form,
        'success': success,  #to drop a little notice like "CONGRATS #WINNING"
    })

@AccountRequired
def developer(request):
    if request.POST:
        request.user.generate_new_api_key()
    return render(request, 'user/developer.html', {})

def old_user_permalink(request, mongo_id):
    try:
        user = User.objects.get(mongo_id = mongo_id)
        return HttpResponsePermanentRedirect(reverse('entity_url', args=[user.username]))
    except:
        raise Http404

def forgot_password(request):
    error = None
    if request.method == 'POST':
        if 'email' in request.POST:
            try:
                u = User.objects.get(email = request.POST['email'].strip(), is_active=True)
                pr = PasswordResetRequest()
                pr.user = u
                pr.uid = str(uuid4().hex)
                pr.save()
                send_notification(type=EmailTypes.RESET_PASSWORD,
                                  user=u,
                                  entity=u,
                                  password_reset_id=pr.uid)
                return render(request, 'user/forgot_password_confirm.html', {})
            except User.DoesNotExist:
                error = "Sorry, this user account does not exist."
            except Exception:
                logging.exception("Error In Forgot Password Post")
                error = "Sorry, an unknown error has occurred."
    return render(request, 'user/forgot_password.html', {
        'error' : error
    })


def reset_password(request, reset_id):
    error = None
    if request.method == 'POST' and 'password' in request.POST and request.POST['password']:
        try:
            p = PasswordResetRequest.objects.get(uid = reset_id)
            u = p.user
            u.password = hash_password(request.POST['password'].strip())
            u.save()

            #perform for all that login magic that happens under the covers
            user = attempt_login(request, u.username, request.POST['password'].strip())
            p.delete()
            return set_auth_cookies(HttpResponseRedirect('/'), user)
        except Exception:
            logging.exception("Error In Reset Password")
            error = 'There was an error resetting your password.'

    return render(request, 'user/reset_password.html', {
        'error' : error,
        'reset_token' : reset_id,
    })

@AccountRequired
@PostOnly
def follow(request, user_id):
    followed = get_object_or_404(User, pk=user_id)
    follow_instance, created = UserToUserFollow.objects.get_or_create(follower=request.user, followed=followed)
    if not follow_instance.is_following:
        follow_instance.is_following = True
        follow_instance.save()
    if created:
        send_notification(type=EmailTypes.FOLLOW,
                user=followed, entity=request.user)
    cache.bust(followed)

    if request.is_ajax():
        button = render_inclusiontag(request, "follow_button followed", "users_tags", {'followed': followed})
        return json_response({'button': button})
    else:
        return redirect(followed)

@AccountRequired
@PostOnly
def unfollow(request, user_id):
    followed = get_object_or_404(User, pk=user_id)
    try:
        follow_instance = UserToUserFollow.objects.get(follower=request.user, followed=followed)
        follow_instance.is_following = False
        follow_instance.stopped_following = datetime.datetime.now()
        follow_instance.save()
    except UserToUserFollow.DoesNotExist:
        pass
    cache.bust(followed)

    if request.is_ajax():
        button = render_inclusiontag(request, "follow_button followed", "users_tags", {'followed': followed})
        return json_response({'button': button})
    else:
        return redirect(followed)

def follower_list(request, user_id):
    start = int(request.GET.get('start', 0))
    end = int(request.GET.get('end', 20))
    user = get_object_or_404(User, id=user_id)
    followers = user.get_active_followers()[start:end]

    html = render_string(request, "user/includes/user_list.html", {
        'users': followers,
        'start_index': start,
        'list_type': 'followers',
    })

    return json_response({
        'html': html,
        'has_more': end < user.get_num_followers,
    })

def following_list(request, user_id):
    start = int(request.GET.get('start', 0))
    end = int(request.GET.get('end', 20))
    user = get_object_or_404(User, id=user_id)
    followings = user.get_active_followings()[start:end]

    html = render_string(request, "user/includes/user_list.html", {
        'users': followings,
        'start_index': start,
        'list_type': 'followings',
    })

    return json_response({
        'html': html,
        'has_more': end < user.get_num_users_following,
    })

@AccountRequired
@PostOnly
def remove_user(request):
    request.user.is_active = False
    request.user.save()
    cache.bust_on_handle(request.user, request.user.username)
    logout(request)
    return unset_auth_cookies(HttpResponseRedirect('/'))
