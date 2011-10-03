import datetime
from django import forms
from django.core.exceptions import ValidationError
from users.models import User, GENDER_CHOICES

REQUIRE_FB_CONNECT = False

class CreateAccountForm(forms.Form):
    first_name = forms.CharField(max_length=50, required=True, label="First Name")
    last_name = forms.CharField(max_length=50, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email")
    password = forms.CharField(required=True, min_length=7, max_length=50, widget=forms.PasswordInput, label="Password")
    location_input = forms.CharField(required=False, label="Location")
    location_data = forms.CharField(required=False)
    redirect_to = forms.CharField(required=False, widget=forms.HiddenInput)

    birth_year = forms.IntegerField(
        required=True,
        label="Year of Birth",
        max_value= datetime.date.today().year,
        min_value= datetime.date.today().year - 120
        )

    gender = forms.ChoiceField(
        required=True,
        label="Gender",
        choices=(('male', 'Male'),('female', 'Female'),),
        widget=forms.RadioSelect
        )

    fb_access_token = forms.CharField(required=REQUIRE_FB_CONNECT)
    fbid = forms.IntegerField(required=REQUIRE_FB_CONNECT)
    bio = forms.CharField(required=False)
    friends = forms.CharField(required=False)
    # if unchecked it returns false and fails the 'is_required' validation
    post_to_facebook = forms.BooleanField(initial=True, required=False )

    def clean(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data.get("email")

        if email:
            try:
                user = User.objects.get(email = email)
                if user:
                    # email is no longer valid - remove it from the cleaned data.
                    self._errors["email"] = self.error_class(['An account with this email address already exists'])
                    del cleaned_data["email"]
            except:
                pass

        if REQUIRE_FB_CONNECT and (not cleaned_data.get('fbid', None) or not cleaned_data.get('fb_access_token', None)):
            self._errors["fbid"] = self.error_class(['Facebook error. Please re-authenticate with Facebook.'])

        if self.data['password'] and len(self.data['password']) < 6:
            self._errors['password'] = self.error_class(['Your password must be at least 6 characters.'])

        if self.data['birth_year']:
            birth_year = 0
            try:
                birth_year = int(self.data['birth_year'])
            except:
                self._errors['birth_year'] = self.error_class(['Please enter a valid year.'])

            max_birth_year = datetime.date.today().year
            min_birth_year = datetime.date.today().year - 120
            if birth_year > max_birth_year:
                self._errors['birth_year'] = self.error_class(['Please enter a year before %s.' % max_birth_year])
            elif birth_year < min_birth_year:
                self._errors['birth_year'] = self.error_class(['Please enter a year after %s.' % min_birth_year])

        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': "Username"}))
    password = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'placeholder': "Password"}))
    redirect_to = forms.CharField(required=False)
    post_auth_action = forms.CharField(required=False)

class UserSettingsForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='E-mail')
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect)
    password = forms.CharField(required=False, min_length=7, max_length=50, label="Change Password",
                               widget=forms.PasswordInput(render_value=False), )
    username = forms.CharField(help_text='http://jumo.com/<b>handle</b>', label='Handle')
    profile_pic = forms.ImageField(required=False, label="Profile Picture")
    location_input = forms.CharField(required=False, label="Location")
    location_data = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ['profile_pic', 'first_name', 'last_name', 'username', 'email', 'password', 'birth_year', 'location_input',
                  'gender', 'bio']

    def clean_email(self):
        try:
            u = User.objects.get(email=self.cleaned_data['email'])
        except User.DoesNotExist:
            return self.cleaned_data['email']

        if not self.instance or u.id != self.instance.id:
            raise ValidationError("An account with this email address already exists.")
        return self.cleaned_data['email']

class PhotoUploadForm(forms.ModelForm):
    profile_pic = forms.ImageField(required=False, label="Profile Picture")

class UserNotificationsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['enable_followed_notification', 'post_to_fb', 'enable_jumo_updates',]

class UserConnectForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['url', 'twitter_id', 'flickr_id', 'youtube_id', 'vimeo_id', 'blog_url']
        widgets = {
            'url': forms.TextInput(attrs={'placeholder':'http://www.joesmith.com'}),
            'twitter_id': forms.TextInput(attrs={'placeholder':'joesmith'}),
            'flickr_id': forms.TextInput(attrs={'placeholder':'joesmith'}),
            'youtube_id': forms.TextInput(attrs={'placeholder':'joesmith'}),
            'vimeo_id': forms.TextInput(attrs={'placeholder':'joesmith'}),
            'blog_url': forms.TextInput(attrs={'placeholder':'http://blog.joesmith.com'}),
        }
