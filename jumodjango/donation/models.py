from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.contrib.contenttypes import generic
from django.db import models, transaction
from etc import cache
from etc.entities import EntityTypes, type_to_class, obj_to_type
from etc.func import crc32, salted_hash
import json
import logging
from org.models import Org
from sourcing.models import SourceTaggedItem
import sys
import urlparse
from users.models import User
#from utils.donations import nfg_api, mock_nfg_api
from utils.misc_helpers import send_admins_error_email


class Donor(models.Model):
    id = models.AutoField(db_column='donor_id', primary_key=True)
    user = models.ForeignKey(User, db_column='user_id', null=True)
    first_name = models.CharField(max_length=30, db_column='first_name')
    last_name = models.CharField(max_length=30, db_column='last_name')
    email = models.EmailField(db_column='email', max_length=200, unique=True)
    email_crc32 = models.IntegerField(db_column='email_crc32')

    class Meta:
        db_table = 'donors'

    @property
    def get_first_name(self):
        return self.first_name

    # For distinguishing in templates between Donors and Jumo users
    @property
    def is_jumo_user(self):
        return self.user and self.user.is_active

    def save(self, *args, **kw):
        self.email = self.email.lower()
        self.email_crc32 = crc32(self.email)
        super(Donor, self).save(*args, **kw)

    @property
    def email_hash(self):
        return salted_hash(self.email)

    @classmethod
    def get_or_create(cls, first_name, last_name, email, user=None):
        email = email.lower()
        d, created = Donor.objects.get_or_create(email=email, email_crc32=crc32(email))
        state_changed = False
        if user and user != d.user:
            d.user = user
            state_changed = True
        else:
            try:
                # For those donating anonymously
                # who are already registered (active) users
                existing_user = User.objects.get(email=email, is_active=True)
                d.user=existing_user
            except User.DoesNotExist:
                pass
        if d.first_name != first_name:
            d.first_name = first_name
            state_changed = True
        if d.last_name != last_name:
            d.last_name = last_name
            state_changed = True

        if state_changed:
            d.save()
        return d

    @classmethod
    def from_email(cls, email):
        try:
            email = email.lower()
            return Donor.objects.get(email=email, email_crc32=crc32(email))
        except Donor.DoesNotExist:
            return None
        except Exception, err:
            logging.exception("Error Retrieving Donor On Email")
            return None

    @classmethod
    def from_user(cls, user):
        try:
            return Donor.objects.get(user=user)
        except Donor.DoesNotExist:
            return None
        except Exception, err:
            logging.exception("Error Retrieving Donor From User")
            return None

    @classmethod
    def get_all_donors_for_entity(cls, entity):
        return Donor.objects.raw("""
        select do.*
        from donations d
        join donors do
            using(donor_id)
        where d.entity_type=%(entity_type)s
        and d.entity_id=%(entity_id)s
        """, {'entity_type': entity.type, 'entity_id': entity.id})

    class Meta:
        db_table = 'donors'

    def is_subscribed_to(self, pub_id):
        return len(self.subscriptions.filter(id=pub_id, subscription__subscribed=True).values_list('id')) > 0


class DonorPhone(models.Model):
    id = models.AutoField(db_column='donor_phone_id', primary_key=True)
    donor = models.ForeignKey(Donor, db_column='donor_id')
    phone = models.CharField(max_length=50)

    class Meta:
        db_table='donor_phone_numbers'


class DonorAddress(models.Model):
    id = models.AutoField(db_column='donor_address_id', primary_key=True)
    donor = models.ForeignKey(Donor, db_column='donor_id', related_name='addresses')
    street1 = models.CharField(max_length=255, db_column='street1')
    street2 = models.CharField(max_length=255, db_column='street2', blank=True)
    city = models.CharField(max_length=255, db_column='city')
    region = models.CharField(max_length=255, db_column='region', blank=True, default="")
    postal_code = models.CharField(max_length=14, db_column='postal_code')
    country = models.CharField(max_length=2, db_column='country', blank=True)
    is_billing = models.BooleanField(default=True, db_column='is_billing')
    is_shipping = models.BooleanField(default=True, db_column='is_shipping')

    class Meta:
        db_table = 'donor_addresses'

    @classmethod
    def get_or_create(cls, **kwargs):
        """
        EX: dict(donor=donor, street1='000 FakeTown', street2='', city='FakeyVille',
                 region='NY', postal_code=10012, country="United States of America")
        """
        da, created = DonorAddress.objects.get_or_create(donor=kwargs["donor"],
                                          street1=kwargs["street1"],
                                          street2=kwargs.get("street2"),
                                          city=kwargs["city"],
                                          region=kwargs["region"],
                                          postal_code=kwargs["postal_code"],
                                          country=kwargs["country"])
        return da


class CreditCard(models.Model):
    id = models.AutoField(db_column='credit_card_id', primary_key=True)
    donor = models.ForeignKey(Donor, db_column='donor_id', related_name='credit_cards')
    donor_address = models.ForeignKey(DonorAddress, db_column='donor_address_id')
    date_last_charged = models.DateTimeField(db_column='date_last_charged')
    status = models.CharField(max_length=50, db_column='status')
    nfg_card_on_file_id = models.IntegerField(db_column='nfg_card_on_file_id')
    nfg_cof_is_active = models.BooleanField(db_column='nfg_cof_is_active')

    class Meta:
        db_table = 'credit_cards'

    class CardStatus:
        """TODO: use statuses to avoid rebilling people we know are failures"""
        DECLINED = 'declined'

    def disable_cof(self):
        pass

class DonationProcessingFailed(Exception):
    pass

class Donation(models.Model):
    id = models.AutoField(db_column='donation_id', primary_key=True)
    donor = models.ForeignKey(Donor, db_column='donor_id', related_name='donations')
    credit_card = models.ForeignKey(CreditCard, db_column='credit_card_id')
    entity_type = models.CharField(max_length=100, db_column='entity_type')
    entity_id = models.IntegerField(db_column='entity_id')
    amount = models.DecimalField(max_digits=19, decimal_places=2, db_column='amount')
    jumo_amount = models.DecimalField(max_digits=19, decimal_places=2, db_column='jumo_amount')
    street1 = models.CharField(max_length=255, db_column='street1')
    street2 = models.CharField(max_length=255, db_column='street2', blank=True)
    city = models.CharField(max_length=255, db_column='city')
    region = models.CharField(max_length=255, blank=True, default="", db_column='region')
    postal_code = models.CharField(max_length=14, db_column='postal_code')
    country = models.CharField(max_length=2, db_column='country', blank=True)
    phone = models.CharField(max_length=50, db_column='phone')
    comment = models.CharField(max_length=2000, db_column='comment', blank=True)
    charge_id = models.IntegerField(db_column='charge_id', null=True, default=None)
    charge_status = models.CharField(max_length=100, db_column='charge_status')
    payment_status = models.CharField(max_length=100, db_column='payment_status')
    last_payment_attempt = models.DateTimeField(db_column='last_payment_attempt')
    date = models.DateTimeField(auto_now_add=True, db_column='donation_date')
    version = models.IntegerField(db_column='version', default=1)
    list_publicly = models.BooleanField(db_column='list_publicly')
    is_anonymous = models.BooleanField(db_column='is_anonymous')


    _source_tagged_items = generic.GenericRelation(SourceTaggedItem,
                                                   content_type_field='item_type',
                                                   object_id_field='item_id')

    class Meta:
        db_table = 'donations'

    class ChargeStatus:
        DO_NOT_ATTEMPT = "do_not_attempt"
        READY = "ready"
        ATTEMPTING_PAYMENT = "attempting_payment"
        PAYMENT_COMPLETE = "payment_complete"

    class PaymentStatus:
        UNPAID = "unpaid"
        PAID = "paid"
        FAILED = "failed"
        PERMAFAILED = "permafailed"

    @classmethod
    def get(cls, id, force_db=False):
        if force_db:
            obj = cls.objects.get(id=id)
            cache.bust(obj)
            return obj
        return cache.get(cls, id)

    @classmethod
    def multiget(cls, ids, force_db=False):
        if force_db:
            return Donation.objects.filter(id__in=ids)
        return cache.get(cls, ids)


    @classmethod
    def get_retryable_donations(cls):
        case_statement = ' '.join(["when %s then %s" % (idx+1,val) for idx, val in enumerate(settings.PAYMENT_RETRY_SCHEDULE) ])
        return Donation.objects.raw("""
        select
        do.*,
        do.last_payment_attempt + interval case count(p.donation_id) """ + case_statement + """ end day as min_retry_date
        from donations do
        join payments p
          on p.donation_id = do.payment_id
          and did_succeed=0
        where do.payment_status = %(failed)s
        and do.charge_status = %(ready)s
        group by do.donation_id
        having utc_timestamp() >= min_retry_date
        """ , {'failed': cls.PaymentStatus.FAILED,
               'ready': cls.ChargeStatus.READY
               })

    @classmethod
    def get_donations_for_entity(cls, entity):
        return Donation.objects.filter(entity_type=entity.type, entity_id=entity.id)

    @classmethod
    def get_processable_donations_for_entity(cls, entity):
        return Donation.objects.filter(entity_type=entity.type,
                                       entity_id=entity.id,
                                       charge_status=cls.ChargeStatus.READY,
                                       payment_status=cls.PaymentStatus.UNPAID)

    @property
    def get_source_tags(self):
        # @todo: not optimized
        return [item.tag for item in self._source_tagged_items.all()]

    @property
    def entity(self):
        return cache.get(type_to_class(self.entity_type), self.entity_id)

    @property
    def get_beneficiaries(self):
        return DonationBeneficiary.objects.filter(donation=self)

    def mark_attempting(self):
        # Optimistic locking
        affected = Donation.objects.filter(id=self.id, version=self.version).update(charge_status=self.ChargeStatus.ATTEMPTING_PAYMENT, version=self.version+1)

        if not affected:
            msg = "Tried optimistic lock of donation row with version %d, but a higher version existed. This is probably BAD. Unless somebody did an ad hoc update, there may be more than 1 instance of bill_campaignd running." % self.version
            send_admins_error_email("DONATION ERROR", msg, sys.exc_info())
            raise DonationProcessingFailed, msg

    def process(self):
        pass

    @transaction.commit_on_success()
    def _execute_payment(self, payment_fails):
        pass


    @classmethod
    def create_and_process(cls, **kwargs):
        pass


    @classmethod
    @transaction.commit_on_success()
    def _create_and_process(cls, **kwargs):
        pass


    @classmethod
    def create_and_store(cls, **kwargs):
        pass

    @classmethod
    @transaction.commit_on_success()
    def _create(cls, store_cc=False, **kwargs):
        pass

    def _to_nfg_dict(self):
        pass

    @classmethod
    def _cc_info_to_nfg_dict(cls, **kwargs):
        pass

    def add_source_tags(self, source_tags):
        pass

    def save(self, *args, **kwargs):
        pass


class DonationBeneficiary(models.Model):
    id = models.AutoField(db_column='donation_beneficiary_id', primary_key=True)
    donation = models.ForeignKey(Donation, db_column='donation_id', related_name='beneficiaries')
    org = models.ForeignKey(Org, db_column='org_id')
    amount = models.DecimalField(max_digits=19, decimal_places=2, db_column='amount')

    class Meta:
        db_table = 'donation_beneficiaries'
        unique_together = ('donation', 'org')

class Payment(models.Model):
    id = models.AutoField(db_column='payment_id', primary_key=True)
    status = models.CharField(max_length=255, db_column='status', blank=True)
    donation = models.ForeignKey(Donation, db_column='donation_id')
    did_succeed = models.BooleanField(db_column='did_succeed')
    error_data = models.CharField(max_length=2000, db_column='error_data')
    payment_date = models.DateTimeField(db_column='payment_date', default=datetime.utcnow)

    class Meta:
        db_table = 'payments'
