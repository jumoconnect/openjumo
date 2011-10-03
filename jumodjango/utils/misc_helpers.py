"""
Oh man, I started a misc module.  I can't wait to see what this turns
into in 3 years.  I'm sorry future me that this has become the dumping
ground you will now have to organize.  Have a beer on me.
"""

def send_admins_error_email(subject, msg, exc_info):
    from django.conf import settings
    from django.core.mail import mail_admins
    import sys
    import traceback

    if settings.DEBUG:
        return
    subject = "Error (CUSTOM): %s" % subject
    tb = '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
    message = "%s\n\n%s" % (msg, tb)
    mail_admins(subject, message, fail_silently=True)
