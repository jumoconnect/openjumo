from datetime import datetime
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404
from donation.models import Donor
from etc import cache
from etc.func import salted_hash
from etc.decorators import AccountRequired
from etc.view_helpers import render
from mailer.models import Unsubscribe, transaction
from mailer.content import pubs, JumoReaderEmail
from message.models import Publication, Subscription
from users.models import User


@transaction.commit_on_success()
def unsubscribe(request):
    id = request.GET['id']
    id_type = request.GET.get('id_type', 'user')
    code = request.GET['code']
    pub = request.GET.get('pub')
    pub_id = request.GET.get('pub_id')

    if id_type == 'user':
        try:
            user = User.objects.get(id=id, is_active=True)
        except ObjectDoesNotExist:
            raise Http404
    elif id_type == 'donor':
        try:
            user = Donor.objects.get(id=id)
        except ObjectDoesNotExist:
            raise Http404
    else:
        raise Http404

    expected_code = salted_hash(user.email)
    if code <> expected_code:
        raise Http404

    if pub:
        pub = pubs[pub]
        publication_id = pub.publication_id
    elif pub_id:
        publication_id = pub_id
    else:
        raise Http404

    pub = Publication.objects.get(id=publication_id)

    unsub, created = Unsubscribe.objects.get_or_create(email=user.email, publication_id=pub.id)

    if pub.user_settings_field:
        # Update user table anyway to allow for resubscription, etc.
        setattr(user, pub.user_settings_field, 0)
        user.save()
        cache.bust_on_handle(user, user.username)
    else:
        try:
            if id_type=='donor':
                sub = Subscription.objects.get(donor=user.id, publication=pub.id)
            elif id_type=='user':
                sub = Subscription.objects.get(user=user.id, publication=pub.id)
            sub.subscribed=False
            sub.save()
            #cache.bust([user, sub])
        except ObjectDoesNotExist:
            raise Http404

    return render(request, 'etc/unsubscribe.html', {'created': created,
                     'user': user,})

@AccountRequired
def jumo_reader(request, username):
    try:
        user = User.objects.get(username = username, is_active=True)
    except ObjectDoesNotExist:
        raise Http404

    if request.user.username <> user.username:
        raise Http404

    msg = JumoReaderEmail(entity=user,
                          user=user,
                          current_user=user,
                          feed_items=[],
                          feed_stream=None,
                          current_time=datetime.now()
                          )

    if 'text' in request.path:
        return HttpResponse(msg.text_content)
    else:
        return HttpResponse(msg.html_content)

@AccountRequired
def notification_email(request, username):
    user = User.objects.get(username = username, is_active=True)
    return render(request, "email/html/notifications/reset_password.html", {
            'hostname' : settings.HTTP_HOST,
            'subject': "You have just become a top advocate for FOO BAR on Jumo.",
            'user' : user,
            'entity' : user})
