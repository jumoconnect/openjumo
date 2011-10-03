from celery.task import task
from mailer.notification_tasks import EmailTypes, send_notification
from donation.models import Donation
#from utils.donations import nfg_api
import logging

@task
def process_donation(donation_id):
    pass
