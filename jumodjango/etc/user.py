
from datetime import datetime
from django.conf import settings
from django.core.cache import cache
from etc import errors, constants
import hashlib
from hashlib import sha256
from hmac import HMAC
import random

NUM_ITERATIONS = 1000

''' HELPER FUNCTIONS '''

def create_salt_cookie(user_id):
    salty = '%s%s' % (user_id, settings.SECRET_KEY)
    h = hashlib.sha1()
    h.update(salty)
    return h.hexdigest()

def check_cookie(user_id, salt):
    test = create_salt_cookie(user_id)
    if test == salt:
        return True
    return False


def hash_password(plain_password):
    salt = _random_bytes(8)
    hashed_password = _pbkdf_sha256(plain_password, salt)
    return salt.encode("base64").strip()+","+hashed_password.encode("base64").strip()


def check_password(saved_password, plain_password):
    salt, hashed_password = saved_password.split(",")
    salt = salt.decode("base64")
    hashed_password = hashed_password.decode("base64")
    return hashed_password == _pbkdf_sha256(plain_password, salt)



def _pbkdf_sha256(password, salt, iterations=NUM_ITERATIONS):
    result = password.encode("utf-8")
    for i in xrange(iterations):
        result = HMAC(result, salt, sha256).digest()
    return result


def _random_bytes(num_bytes):
    return "".join(chr(random.randrange(256)) for i in xrange(num_bytes))
