from django.contrib.localflavor.us.us_states import STATE_CHOICES
from django.core.exceptions import ValidationError
from django import forms
from django.forms.util import ErrorList
from etc.country_field import COUNTRIES
from etc.credit_card_fields import CreditCardField, ExpiryDateField, VerificationValueField
#from utils.donations import nfg_api


"""
    Unused errors.
    InvalidCardOnFile, NpoNotFound, NpoNotEligible, InvalidDonorIpAddres,
    InvalidDonationType, NoChangeRequested, CountryNotSupported, InternationalDonationsNotSupported,
    COFNotFound, COFAlreadyDeleted, COFInUse, COFNoRefCode, UserNotFound, InvalidDonorToken
"""

class BaseDonationForm(forms.Form):

    CUST_STATE_CHOICES = list(STATE_CHOICES)
    CUST_STATE_CHOICES.insert(0,('', '---------'),)

    #FIELDS
    donor_email = forms.EmailField(label="Email", required=True)
    first_name = forms.CharField(label="First Name", max_length=30, required=True)
    last_name = forms.CharField(label="Last Name", max_length=30, required=True)
    address_line_one = forms.CharField(label="Address", required=True)
    address_line_two = forms.CharField(required=False)
    city = forms.CharField(label="City", required=True)
    state = forms.CharField(label="State", required=False, widget=forms.Select(choices=CUST_STATE_CHOICES))
    zip_code = forms.CharField(required=True, label="Zip Code")
    country = forms.ChoiceField(label="Country", choices=COUNTRIES, required=True)
    phone = forms.CharField(label="Phone", max_length=50, required=True)
    donation_amount = forms.DecimalField(label="Donation", required=True, min_value=10.0, max_value=20000.0,
                                         error_messages={"min_value":"The minimum donation amount is $10.00.",
                                                         "max_value":"The maximum donation amount is $20,000.",})
    jumo_amount = forms.DecimalField(label="Optional tip for Jumo", required=True, min_value=0.0)
    name_on_card = forms.CharField(label="Name On Card", max_length=60, required=True)
    card_number = CreditCardField(label="Credit Card Number", required=True)
    expiry_date = ExpiryDateField(label="Expiration Date", required=True)
    ccv_code = VerificationValueField(label="CCV", required=True)

    comment = forms.CharField(label="Why are you pledging?", max_length=300, required=False,
                              widget=forms.Textarea(attrs={"rows":3,"cols":72}))

    post_to_facebook = forms.BooleanField(label="Share this donation Facebook", initial=True, required=False)
    list_name_publicly = forms.BooleanField(label="Share this donation on Jumo", initial=True, required=False)

    def __init__(self, initial_user=None, initial_amount=None, *args, **kwargs):
        super(BaseDonationForm, self).__init__(*args, **kwargs)
        if initial_user and not self.is_bound:
            self.user_donating = initial_user
            self.fields["donor_email"].initial = initial_user.email
            self.fields["first_name"].initial = initial_user.first_name
            self.fields["last_name"].initial = initial_user.last_name
            self.user_donating = initial_user
        if initial_amount:
            self.fields["donation_amount"].initial = initial_amount

    def to_donation_data(self, donor_user=None, use_mock_nfg=False, sources=None):
        #pretty sure this will blow up if data isn't valid.
        return dict(firstname=self.cleaned_data["first_name"],
                    lastname=self.cleaned_data["last_name"],
                    email=self.cleaned_data["donor_email"],
                    user_donating=donor_user,
                    phone=self.cleaned_data["phone"],
                    street1=self.cleaned_data["address_line_one"],
                    street2=self.cleaned_data["address_line_two"],
                    city=self.cleaned_data["city"],
                    region=self.cleaned_data["state"],
                    postal_code=self.cleaned_data["zip_code"],
                    country=self.cleaned_data["country"],
                    name_on_card=self.cleaned_data["name_on_card"],
                    cc_number=self.cleaned_data["card_number"],
                    cc_type=self.cleaned_data["card_type"],
                    cc_exp_month=self.cleaned_data["expiry_date"].month,
                    cc_exp_year=self.cleaned_data["expiry_date"].year,
                    cc_csc=self.cleaned_data["ccv_code"],
                    amount=self.cleaned_data["donation_amount"],
                    jumo_amount=self.cleaned_data["jumo_amount"],
                    comment=self.cleaned_data["comment"],
                    list_publicly = self.cleaned_data["list_name_publicly"],
                    use_mock_nfg = use_mock_nfg,
                    sources = sources
                    )

    def handle_nfg_errors(self, nfg_errors):
        for nfg_err in nfg_errors:
            if nfg_err.get("error_code") and NFG_ERROR_TO_FIELD.get(nfg_err["error_code"]):
                fieldname = NFG_ERROR_TO_FIELD[nfg_err["error_code"]]
                if not self._errors.get(fieldname):
                    self._errors[fieldname] = ErrorList([nfg_err["error_data"]])
                else:
                    self._errors[fieldname].append(nfg_err["error_data"])
            else:
                self.handle_unknown_error()

    def handle_unknown_error(self):
        #We're just setting the error so the template knows it's there.
        #It doesn't actually use the error message.
        self._errors["unknown"] = ErrorList(["We're unable to process your donation. Ensure that the address and zipcode provided match the billing address on your credit card and that the CCV number is correct."])



class StandardDonationForm(BaseDonationForm):
    def to_donation_data(self, org, *args, **kwargs):
        data = super(StandardDonationForm, self).to_donation_data(*args, **kwargs)
        data["entity"] = org
        data["beneficiary"] = org
        return data



class StillDonateForm(forms.Form):
    still_donate = forms.BooleanField(required=False, widget=forms.RadioSelect(choices=((False, 'No'),(True, 'Yes'),)), initial=True)

    def handle_unknown_error(self):
        #We're just setting the error so the template knows it's there.
        #It doesn't actually use the error message.
        self._errors["unknown"] = ErrorList(["An Unknown Error Has Occurred"])
