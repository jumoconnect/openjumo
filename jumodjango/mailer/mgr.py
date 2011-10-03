from datetime import datetime
from django.core.mail import EmailMessage
from django.conf import settings
import logging
from mailer.reader_tasks import send_jumo_reader_email
from users.models import User
"""
def send_mail():
    if settings.DEBUG:
        msgs = Email.objects.filter(sent = False).filter(recipient__icontains = '@jumo.com')
    else:
        msgs = Email.objects.filter(sent = False)
    if not msgs:
        logging.info('No email to send.')
    while True:
        if settings.DEBUG:
            try:
                msg = Email.objects.filter(sent = False).filter(recipient__icontains = '@jumo.com')[0]
                _mark_as_sent(msg)
                try:
                    e = EmailMessage(msg.subject, msg.body, 'no-reply@jumo.com', [msg.recipient])
                    send_msg(e)
                except:
                    continue
            except:
                break
        else:
            try:
                msg = Email.objects.filter(sent = False)[0]
                _mark_as_sent(msg)
                try:
                    e = EmailMessage(msg.subject, msg.body, 'no-reply@jumo.com', [msg.recipient])
                    send_msg(e)
                except:
                    continue
            except:
                break
"""


def jumo_reader(num_users=None):
    users_to_email =  User.objects.filter(is_active=True, next_email_time__lte=datetime.now(), email_stream_frequency__gt=0)
    if num_users is None:
        users_to_email = users_to_email.iterator()
    else:
        users_to_email = users_to_email.order_by('?')[:num_users]

    #for user in users_to_email.iterator():
    for user in users_to_email:
        try:
            send_jumo_reader_email.delay(user, [])
        except Exception, e:
            logging.error('Uh-oh, had an issue sending an e-mail to user %s' % user.id, e)
