from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import get_connection
from django.conf import settings

class JumoEmailBackend(EmailBackend):
    def send_messages(self, email_messages):
        for msg in email_messages:
            super(JumoEmailBackend, self).send_messages([msg])
    def send(self, msg):
        super(JumoEmailBackend, self).send_messages([msg])


