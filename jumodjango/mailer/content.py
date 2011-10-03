from mailer.models import Email

from etc.func import salted_hash
from etc.view_helpers import url_with_qs
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
import settings
import inspect
import random
import sys

class EmailTypes:
    JUMO_READER = 'news_email'
    FOLLOW = 'follow'
    MOST_ACTIVE = 'most_active'
    COMMENT = 'comment'
    RESET_PASSWORD = 'reset_password'
    CLAIM_ORG = 'claim_org'
    POSTED_ON_PROFILE = 'posted_on_profile'
    DONATION_FAILURE = 'donation_failure'

class EmailTextHTML(object):
    """Proxy to Email model"""
    headers = {}

    def __init__(self, type, user=None, email_address=None, subject='', update_next_email_time=False, **kw):
        hostname = settings.HTTP_HOST
        email_address = email_address if email_address else user.email
        unsub_code = salted_hash(email_address)
        kw.update(dict(hostname=hostname,
                       subject=subject,
                       user=user,
                       unsub_code=unsub_code))
        self.subject = subject
        self.template_args = kw
        self.text_content = render_to_string('email/txt/%s.txt' % type, kw)
        self.html_content = render_to_string('email/html/%s.html' % type, kw)
        self.user = user
        self.update_next_email_time=update_next_email_time

        # Lock that down
        if settings.EMAIL_REAL_PEOPLE or email_address.endswith('@jumo.com'):
            self.to = email_address
        else:
            self.to = 'jumodev@gmail.com'
        self.from_address = 'Jumo <no-reply@jumo.com>'

    def send(self):
        msg = Email(subject=self.subject, body=self.text_content, html=self.html_content,
                    user=self.user, recipient=self.to, from_address=self.from_address,
                    headers = self.headers)
        msg.send(self.update_next_email_time)

class JumoReaderEmail(EmailTextHTML):
    headers = {'X-SMTPAPI': '{"category": "Jumo Reader"}'}
    publication = 'reader'
    publication_id = 1
    user_sub_field = 'email_stream_frequency'

    def _get_random_stats(self, user):
        issues = [issue for issue in user.get_all_issues_following if issue.get_all_statistics]
        stats = [issue.get_all_statistics for issue in issues]
        flat_stats = [y for x in stats for y in x]

        random.shuffle(flat_stats)
        return flat_stats

    def __init__(self, user, **kw):
        random_stats = self._get_random_stats(user)[:1]
        super(JumoReaderEmail, self).__init__(type=EmailTypes.JUMO_READER,
                                              user=user,
                                              subject='Jumo Reader | Top News on the Issues You Care About',
                                              update_next_email_time=True,
                                              random_stats = random_stats,
                                              publication_id = self.publication_id,
                                              **kw)

class NotificationEmail(EmailTextHTML):
    """Important: make sure you add a type member to any subclasses"""
    publication = 'notifications'
    publication_id = 2

    def __init__(self, type, subject, user, entity, **kw):
        type='notifications/%s' % type
        super(NotificationEmail, self).__init__(type=type,
                                                user=user,
                                                subject=subject,
                                                entity=entity,
                                                publication_id = self.publication_id,
                                                **kw)

class FollowEmail(NotificationEmail):
    type = EmailTypes.FOLLOW

    def __init__(self, user, entity, **kw):
        super(FollowEmail, self).__init__(type = self.type,
                                          subject = '%s started following you on Jumo' % entity.get_name.title(),
                                          user = user,
                                          entity = entity)


class BadgeEmail(NotificationEmail):
    type = EmailTypes.MOST_ACTIVE
    def __init__(self, user, entity, **kw):
        super(BadgeEmail, self).__init__(type = self.type,
                                         subject = "You are now a top advocate for %s on Jumo" % entity.get_name.title(),
                                         user = user,
                                         entity = entity)

class CommentEmail(NotificationEmail):
    """
    e = EmailMessage('Jumo | %s commented on your Jumo story!' % request.user.get_name, 'Hi %s,\n\n%s commented on a story you posted on Jumo.\n\n"%s"\n\nView or reply by following the link below:\nhttp://jumo.com/story/%s\n\nThanks,\nThe Jumo Team' % (fi.poster.get_name, request.user.get_name, request.POST['comment'], fi.id), 'no-reply@jumo.com', [fi.poster.email])
                    e.send_now = True
                    e.send()
    """

    type = EmailTypes.COMMENT
    def __init__(self, user, entity, feed_item, comment):
        super(CommentEmail, self).__init__(type = self.type,
                                           subject = "%s commented on your Jumo story" % entity.get_name.title(),
                                           user = user,
                                           entity = entity,
                                           feed_item = feed_item,
                                           comment = comment)

class PostedOnProfileEmail(NotificationEmail):
    """
    Hi Kristen Titus,

    Matt Langer posted to your Jumo profile:

    "HEADLINE: Man eats hot dogs for dinner. Support childhood obesity."

    View or reply by following the link below:
    http://www.jumo.com/user/4cd8937ca70f66b06ac5b9d7

    Thanks,
    The Jumo Team
    """
    type = EmailTypes.POSTED_ON_PROFILE
    def __init__(self, user, entity, feed_item):
        super(PostedOnProfileEmail, self).__init__(type=self.type,
                                                   subject = "%s posted to your Jumo profile" % entity.get_name.title(),
                                                   user = user,
                                                   entity = entity,
                                                   feed_item = feed_item,
                                                   )


class ResetPasswordEmail(NotificationEmail):
    """"e = EmailMessage('Reset your password on Jumo.', 'Hi %s,\n\nClick the following link to be automatically logged into Jumo: http://jumo.com/reset_password/%s\n\nthe Jumo team' % (u.first_name, pr.uid), 'no-reply@jumo.com', [email])"""
    type = EmailTypes.RESET_PASSWORD
    def __init__(self, user, entity, password_reset_id):
        super(ResetPasswordEmail, self).__init__(type=self.type,
                                                 subject = "Reset your password on Jumo",
                                                 user = user,
                                                 entity = None,
                                                 password_reset_id = password_reset_id
                                                 )

class ClaimOrgEmail(NotificationEmail):
    """"e = EmailMessage('Become the administrator of %s on Jumo.' % o.get_name, 'Hi %s,\n\nClick the following link to verify your affiliation with %s: http://jumo.com/org/claim/%s/confirm/%s\n\nthe Jumo team' % (request.user.first_name, o.get_name, o.id, o.claim_token), 'no-reply@jumo.com', [info['email']])"""
    type = EmailTypes.CLAIM_ORG
    def __init__(self, user, entity, org_claim_token):
        super(ClaimOrgEmail, self).__init__(type=self.type,
                                                 subject = "Become the administrator of %s on Jumo" % entity.get_name.title(),
                                                 user = user,
                                                 entity = entity,
                                                 org_claim_token = org_claim_token,
                                                 )


class DonationFailureEmail(NotificationEmail):
    type = EmailTypes.DONATION_FAILURE
    def __init__(self, user, entity):
        super(DonationFailureEmail,self).__init__(type=self.type,
                                                  subject='Jumo Billing | Charge Unsucessful',
                                                  user = user,
                                                  entity = entity)


class JumoUpdateEmail(EmailTextHTML):
    publication = 'updates'
    publication_id = 3
    user_sub_field = 'enable_jumo_updates'


class UserDefinedEmail(EmailTextHTML):
    def __init__(self, type, user_or_donor, message, **kw):
        super(UserDefinedEmail, self).__init__(type=type,
                                               email_address=user_or_donor.email,
                                               subject=message.subject,
                                               publication_id = message.publication_id,
                                               message=message,
                                               **kw
                                               )


# Using inspect so we don't have to add new notifications manually
# Just make sure you add type to all new NotificationEmail classes
notifications = dict((cls.type, cls) for name, cls in inspect.getmembers(sys.modules[__name__])
                     if inspect.isclass(cls)
                     and issubclass(cls, NotificationEmail)
                     and hasattr(cls, 'type'))


pubs = dict((cls.publication, cls) for name, cls in inspect.getmembers(sys.modules[__name__])
                     if inspect.isclass(cls)
                     and issubclass(cls, EmailTextHTML)
                     and hasattr(cls, 'publication'))
