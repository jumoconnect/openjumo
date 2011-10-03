from django.db import models
from users.models import User
from org.models import Org
from django.db import transaction
from django.db.models import Q
from etc import cache

from django.db.models.query import QuerySet
from django.db.models import F
from django.db.models.loading import get_model

from datetime import datetime

# Constant publication_id for notifications
NOTIFICATIONS_PUB = 2

class Subscription(models.Model):
    id = models.AutoField(db_column='subscription_id', primary_key=True)
    user = models.ForeignKey(User, db_column='user_id', null=True)
    donor = models.ForeignKey('donation.Donor', db_column='donor_id', null=True)
    publication = models.ForeignKey('message.Publication', db_column='publication_id')
    subscribed = models.BooleanField(db_column='subscribed')

    class Meta:
        db_table = 'subscriptions'

    @classmethod
    def get_or_create(cls, pub_id=None, donor=None, user=None):
        sub = None
        created = False
        try:
            if (user or donor.user) and donor:
                sub = Subscription.objects.get(Q(donor=donor) | Q(user=donor.user), publication=pub_id)
            elif user or donor.user:
                u = user or donor.user
                sub = Subscription.objects.get(user=u, publication=pub_id)
            else:
                sub = Subscription.objects.get(donor=donor, publication=pub_id)
        except Subscription.DoesNotExist:
            sub = Subscription(user=user or donor.user, donor=donor, publication_id=pub_id, subscribed=True)
            created = True
        else:
            # This is the reason I'm overriding get_or_create
            # The subscription exists, but set the user at least in case they've since become one
            sub.user = user or donor.user
        return sub, created

class NoMessagesRemaining(Exception):
    pass

class Publication(models.Model):
    id = models.AutoField(db_column='publication_id', primary_key=True)
    title = models.CharField(max_length=255, db_column='title')
    default_subject = models.CharField(max_length=255, db_column='default_subject')
    is_staff_pub = models.BooleanField(db_column='is_staff_publication')
    user_settings_field = models.CharField(max_length=255, db_column='user_settings_field', null=True)
    max_subscriber_emails = models.IntegerField(db_column='max_subscriber_emails')
    subscriber_emails_sent = models.IntegerField(db_column='subscriber_emails_sent', default=0)


    users = models.ManyToManyField(User, through='Subscription', null=True, related_name='subscriptions')
    donors = models.ManyToManyField('donation.Donor', through='Subscription', null=True, related_name='subscriptions')
    admins=models.ManyToManyField(User, through='PubAdmin', null=True, related_name='publications_admin_for')

    class Meta:
        db_table = 'publications'

    @classmethod
    def get(cls, id, force_db=False):
        if force_db:
            return Message.objects.get(id=id)
        return cache.get(cls, id)



    def subscribe(self, donor, resubscribe=False):
        # Check to see they're not already subscribed
        sub, created = Subscription.get_or_create(donor=donor, pub_id=self.id)
        # In case the user has since been created
        sub.user=donor.user

        if created or resubscribe:
            sub.subscribed=True  # Otherwise use whatever the previous subscription status was

        sub.save()
        return sub, created

    def get_subscribed_user_ids(self):
        """
        # Not using the user_settings_field part yet, just playing with the idea,
        # not sure I want the multiget to get every single user in one go for Jumo Reader though
        if self.user_settings_field:
            settings_field = self.user_settings_field
            val = True
            if settings_field == 'email_stream_frequency':
                settings_field = self.user_settings_field + '__gt'
                val = 0
            return User.objects.filter(**{settings_field: val, 'is_active': True}).iterator()
        """

        # Coerces the returned rows into a flat list, and returns an iterator over them.
        # so return value should be like [1, 2, 4, 4389, 23895,98359]
        return Subscription.objects.filter(publication=self,
                                           subscribed=True).values_list('user_id', flat=True).iterator()

    def get_subscribed_donor_ids(self):
        # Coerces the returned rows into a flat list, and returns an iterator over them.
        # so return value should be like [1, 2, 4, 4389, 23895,98359]
        return Subscription.objects.filter(publication=self,
                                           subscribed=True).values_list('donor_id', flat=True).iterator()

    @property
    @cache.collection_cache('users.User', '_admin_ids')
    def get_admins(self):
        return self.admins.all()

class PubAdmin(models.Model):
    id = models.AutoField(db_column='pub_admin_id', primary_key=True)
    user = models.ForeignKey(User, db_column='user_id')
    publication = models.ForeignKey(Publication, db_column='publication_id')

    class Meta:
        db_table = 'pub_admins'

class Message(models.Model):
    id = models.AutoField(db_column='message_id', primary_key=True)
    publication = models.ForeignKey(Publication, db_column='publication_id')
    subject = models.CharField(max_length=255, db_column='subject')
    confirmed = models.BooleanField(db_column='confirmed')
    sent = models.BooleanField(db_column='sent')
    date_created = models.DateTimeField(db_column='date_created', default=datetime.utcnow)

    class Meta:
        db_table = 'messages'

    @property
    def get_url(self):
        return '/message/%s' % self.subject


    @classmethod
    def get(cls, id, force_db=False):
        if force_db:
            return Message.objects.get(id=id)
        return cache.get(cls, id)

    @classmethod
    def multiget(cls, ids, force_db=False):
        if force_db:
            # For sorting
            message_dict = dict((message.id, message) for message in Message.objects.filter(id__in=ids))
            return [message_dict[id] for id in ids]
        return cache.get(cls, ids)

    @classmethod
    def create(cls, publication_id, subject, email=True):
        message = Message(publication_id=publication_id, subject=subject, confirmed=False, sent=False)
        if not email:
            # GAHHH do something different here
            message.confirmed = True
            message.sent = True
        message.save()
        return message

    @classmethod
    @transaction.commit_on_success()
    def confirm(cls, message_id):
        message = Message.objects.get(id=message_id)
        # Increment subscriber_emails_sent for the publication by 1 atomically
        # Return the rows affected by the update. Since we've included the "< max_subscriber_emails" condition
        # in the WHERE clause, the update would not change any rows for a campaign that has used up all its e-mails
        affected = Publication.objects.filter(id=message.publication_id, subscriber_emails_sent__lt=F('max_subscriber_emails')).update(subscriber_emails_sent = F('subscriber_emails_sent') + 1)
        if not affected:
            raise NoMessagesRemaining('This publication has no messages remaining')     # Rolls back the transaction
        cache.bust(message.publication)

        message.confirmed=True
        message.save()
        return message
