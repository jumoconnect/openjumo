from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import email_re
from etc.user import check_password

class JumoBackend:
    def authenticate(self, username=None, password=None):
        if email_re.match(username):
            try:
                _user = User.objects.get(email = username, is_active = True)
            except:
                return None
        else:
            try:
                _user = User.objects.get(username = username, is_active = True)
            except:
                return None
        if check_password(_user.password, password):
            return _user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id, is_active = True)
        except User.DoesNotExist:
            return None
