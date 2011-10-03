from celery.task import task
from datetime import datetime
import logging
from mailer.content import JumoReaderEmail

@task(rate_limit='100/s')
def send_jumo_reader_email(user, most_popular_stories):
    logging.debug('Getting feed stream for user: %s' % user.id)
    days_back = user.email_stream_frequency/86400

    logging.debug('Found %s feed items' % len(feed_items))
    if len(feed_items) < 3:
        # feed_items = (feed_items + most_popular_stories)[:3]
        logging.warning("You no give me three quality stories, I no send e-mail...")
        return

    logging.debug('Generating template for message...')
    msg = JumoReaderEmail(entity=user,
                          user=user,
                          current_user=user,
                          feed_items=[],
                          feed_stream=None,
                          current_time=datetime.now()
                          )

    logging.debug('Cool! Generated.')
    msg.send()
    logging.debug('Sent message to %s' % user.email)
    return user.email
