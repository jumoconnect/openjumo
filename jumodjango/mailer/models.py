from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.core.mail.message import EmailMultiAlternatives
from django.db import models, transaction
from users.models import User


class Unsubscribe(models.Model):
    email = models.CharField(max_length=200, db_column='email')
    publication_id = models.IntegerField(db_column='publication_id')
    date_created = models.DateTimeField(default=datetime.now(), db_column='date_created')

    class Meta:
        db_table = 'unsubscribes'

class Email(models.Model):
    sent = models.BooleanField(default = False, db_column='sent')
    user = models.ForeignKey(User, db_column='user_id', related_name='emails', null=True)
    from_address = None
    recipient = models.EmailField(db_column='recipient')
    headers = None
    subject = models.CharField(max_length = 255, db_column='subject')
    body = ""
    html = ""
    date_created = models.DateTimeField(default = datetime.now, db_column='date_created')
    date_sent = models.DateTimeField(blank = True, null = True, db_column='date_sent')

    _field_set = None

    @classmethod
    def get_field_set(cls):
        if not cls._field_set:
            cls._field_set = set([field.name for field in cls._meta.fields])
        return cls._field_set

    def __init__(self, **kw):
        """
        So the object's constructor can behave like a regular model but we don't have
        to actually write all the data to the DB
        """
        fields = self.get_field_set().intersection(kw)
        new_args = dict((field, kw.pop(field)) for field in fields)
        super(Email, self).__init__(**new_args)

        user_or_donor = kw.get('user')
        if hasattr(user_or_donor, 'user'):
            kw['user'] = kw['user'].user

        for k, v in kw.iteritems():
            setattr(self, k, v)


    class Meta:
        db_table = 'mailer_email'

    @transaction.commit_on_success()
    def send(self, update_next_email_time=False):
        msg = None
        if self.html:
            msg = EmailMultiAlternatives(self.subject, self.body, self.from_address, to=[self.recipient], headers = self.headers)
            msg.attach_alternative(self.html, "text/html")
        else:
            msg = EmailMessage(self.subject, self.body, self.from_address, [self.recipient])
        self.sent = True
        now = datetime.utcnow()
        self.date_sent=now
        if update_next_email_time:
            self.user.next_email_time = datetime.date(now + timedelta(seconds=self.user.email_stream_frequency))
            self.user.save()
        self.save()
        msg.send()
