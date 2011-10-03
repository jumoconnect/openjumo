from django.core.exceptions import ValidationError
from django.test import TestCase
from users.models import User

REQUIRED_USER_FIELDS = {'username':'testing', 'long_email':'fake@fake.com', 'password':'fake'}

class UserTestCase(TestCase):
    fixtures = []

    def test_required_fields(self):
        # Test minimum set of fields required for new user to pass validations
        u = User(**REQUIRED_USER_FIELDS)
        u.full_clean()

        # Validation should fail when no username is provided
        u = User(**self._req_fields_without('username'))
        self.assertRaises(ValidationError, u.full_clean)

        # Validation should fail when no email is provided
        u = User(**self._req_fields_without('long_email'))
        self.assertRaises(ValidationError, u.full_clean)

        # Validation should fail when no password is provided
        u = User(**self._req_fields_without('password'))
        self.assertRaises(ValidationError, u.full_clean)

    def _req_fields_without(self, field_name):
        f = REQUIRED_USER_FIELDS.copy()
        f.update({field_name:''})
        return f
