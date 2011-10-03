from celery.task import task
from donation.models import Donor
import logging
from message.models import Message, Publication
import socket


@task(ignore_result=True, rate_limit='10/s')
def _send_user_message(message_id, campaign_id):
    message = Message.get(message_id)
    pub_id = message.publication_id
    publication = Publication.get(pub_id)
    donor_ids = publication.get_subscribed_donor_ids()

    for donor_id in donor_ids:
        _email_donor.delay(donor_id, message.id)

def send_user_message(message_id):
    """ Make this call appear synchronous. Usage:

    send_user_message(1)

    Actually an asynchronous task
    """

    try:
        _send_user_message.delay(message_id)
    except socket.timeout:
        logging.error("Couldn't send message due to socket timeout. Rabbit may be down")
