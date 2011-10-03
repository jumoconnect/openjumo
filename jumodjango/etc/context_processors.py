from django.conf import settings

def general(request):
    return {
        'settings' : settings,
        'user' : request.user,
        'request' : request,
    }
