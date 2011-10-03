from celery.task import task
from donation.models import Donor
import logging
from mailer.content import notifications, EmailTypes #This is being imported from this module by many others.
import socket

NOTIFICATIONS_PUB = 2

@task(ignore_result=True, default_retry_delay=10)
def _send_notification(type, user, entity, force_send=False, **kw):
    email_cls = notifications.get(type)

    # Both donor and user have this method
    if (force_send or user.is_subscribed_to(NOTIFICATIONS_PUB)) and (isinstance(user, Donor) or user.is_active):
        msg = email_cls(user=user, entity=entity, **kw)
        try:
            msg.send()
            logging.info("Sent message to %s" % user.email)
            return user.email
        except Exception, exc:
            logging.exception('Got an error while sending e-mail: %s' % exc)
            _send_notification.retry(exc=exc)

    else:
        logging.info("User is unsubscribed, not sending")

def send_notification(type, user, entity, **kw):
    try:
        _send_notification.delay(type, user, entity, **kw)
    except socket.timeout:
        logging.error("Couldn't send message due to socket timeout. Rabbit may be down")
