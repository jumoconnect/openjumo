from django import template
from django.conf import settings
from lib.disqus import get_sso_auth

from issue.models import Issue
from org.models import Org
from users.models import User

'''
        required context for template:
            # general disqus config
            forum_shortname (settings)
            dev_mode (settings)
            
            # page/thread specific
            thread_uid <settings.dev_mode>_<entity.type>_<entity.id>
            thread_ref_url # needs to be full qualified url
            thread_title
            
            # sso auth
            public_api_key (settings)
            sso_auth_msg (lib/disqus.get_sso_auth_msg)
            
            # sso display
            login_url
            logout_url
            small_logo_img
            sign_in_img
'''
register = template.Library()

@register.inclusion_tag("disqus/comment_thread.html", takes_context=True)
def disqus_comment_thread(context):    
    user = context['user']
    entity = context['entity']
    
    # add all the context needed for thread display code
    context['forum_name'] = settings.DISQUS_FORUM_NAME
    context['dev_mode'] = settings.DISQUS_DEV_MODE
    context['thread_uid'] = get_entity_thread_uid(entity)
    context['thread_ref_url'] = 'http://www.jumo.com%s' % (entity.get_url) 
    context['thread_title'] = '%s' % (entity.get_name)
    context['public_api_key'] = settings.DISQUS_PUBLIC_KEY
    context['sso_auth_msg'] = get_sso_auth( user )
    context['login_url'] = '/login?post_auth_action=close'
    context['logout_url'] = '/logout' # note, might need redirect to same page
    context['small_logo_img'] = 'favicon.png'
    context['sign_in_img'] = 'img/login.png'
    
    return context
    
@register.inclusion_tag("disqus/comment_count.html", takes_context=True)
def disqus_comment_count(context):
    entity = context['entity']
    
    # add all the context needed for comment count display code
    context['forum_name'] = settings.DISQUS_FORUM_NAME
    context['thread_uid'] = get_entity_thread_uid(entity)    
    
    return context


def get_entity_thread_uid(entity):
    entity_type = None
    if isinstance(entity, Issue):
        entity_type = 'issue'
    elif isinstance(entity, Org):
        entity_type = 'org'
    elif isinstance(entity, User):
        entity_type = 'user'
    
    # note: prefix comment thread unique id's in dev environments to
    # avoid conflicts with production threads
    devprefix = ''
    if settings.DISQUS_DEV_MODE == 1:
        devprefix = 'dev_'
    
    return '%s%s_%s' % (devprefix, entity_type, entity.id)
