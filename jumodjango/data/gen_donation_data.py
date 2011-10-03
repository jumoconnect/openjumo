#!/usr/bin/env python
# django environment setup

import sys,os
sys.path.append(os.path.realpath(os.sep.join([os.path.dirname(__file__), os.pardir])))

from django.core.management import setup_environ
import settings
setup_environ(settings)

# Have to do this cache._populate bit or get_model calls will try to do an import
# and cause circular import hell
from django.db.models.loading import cache
cache._populate()

import codecs
from django.core import serializers
from django.contrib.auth.models import User as AuthUser

from issue.models import Issue
from users.models import User
from org.models import Org
from users.models import Location
from donation.models import *
from message.models import Publication, Subscription, Message


donations = list(Donation.objects.all()[:5])


payments = Payment.objects.filter(donation__in=donations)

donors = Donor.objects.filter(donations__in=donations)
users = User.objects.filter(id__in = [d.user.id for d in donors if d])
beneficiaries = DonationBeneficiary.objects.filter(donation__in=donations)
donor_addresses = DonorAddress.objects.filter(donor__in=donors)
donor_phones = DonorPhone.objects.filter(donor__in=donors)
credit_cards = CreditCard.objects.filter(donor__in=donors)

attempting_donation = donations[0]
attempting_donation.charge_status = Donation.ChargeStatus.ATTEMPTING_PAYMENT
attempting_donation.id = 1
dontattempt_donation = donations[1]
dontattempt_donation.charge_status = Donation.ChargeStatus.DO_NOT_ATTEMPT
dontattempt_donation.id = 2
complete_donation = donations[2]
complete_donation.charge_status = Donation.ChargeStatus.PAYMENT_COMPLETE
complete_donation.id = 3
paid_donation = donations[3]
paid_donation.payment_status = Donation.PaymentStatus.PAID
paid_donation.id = 4
permafail_donation = donations[4]
permafail_donation.payment_status = Donation.PaymentStatus.PERMAFAILED
permafail_donation.id = 5



dons = [attempting_donation, dontattempt_donation, complete_donation, paid_donation, permafail_donation]

fixtures = list(dons) + list(users) + list(donors) + list(beneficiaries) + list(donor_addresses) + list(donor_phones) + list(credit_cards)

data = serializers.serialize('json', fixtures, indent=4)
data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures/donation_test_data.json")
fh = codecs.open(data_file, 'w', encoding='UTF-8')
fh.write(data)
fh.close()
print "Data written to %s" % data_file
