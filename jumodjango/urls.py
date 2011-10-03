from api.api_v1 import api_urls
from django.conf.urls.defaults import *
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
)

''' RANDOM URLs '''

urlpatterns += patterns('etc.views',
    url(r'^about/?$', 'about', name = 'about'),
    url(r'^help/?$', 'help', name = 'help'),
    url(r'^jobs/?$', 'jobs', name = 'jobs'),
    url(r'^team/?$', 'team', name = 'team'),
    url(r'^blog/?$', 'blog', name = 'blog'),
    url(r'^contact/?$', 'contact', name = 'contact'),
    url(r'^privacy/?$', 'privacy', name = 'privacy'),
    url(r'^terms/?$', 'terms', name = 'terms'),
    url(r'^/?$', 'index', name = 'index'),
    url(r'^error/?$', 'throw_error', name = 'throw_error'),
    url(r'^health_check/?$', 'health_check', name = 'health_check'),
)

''' END OF RANDOM URLs '''



''' API URLS '''

urlpatterns += patterns('',
    (r'^api/', include(api_urls())),
)

''' END API URLS '''


''' USER URLs '''

urlpatterns += patterns('users.views',
    url(r'^login/?$', 'login_permalink', name = 'login_permalink'),
    url(r'^logout/?$', 'logout_permalink', name = 'logout_permalink'),
    url(r'^setup/?$', 'setup', name = 'setup'),
    url(r'^discover/?$', 'discover', name = 'discover'),
    url(r'^user/(?P<mongo_id>[a-zA-Z0-9\-_].*)/?$', 'old_user_permalink', name = 'old_user_permalink'),
    url(r'^forgot_password/?$', 'forgot_password', name = 'forgot_password'),
    url(r'^reset_password/(?P<reset_id>[a-fA-F0-9].*)/?$', 'reset_password', name = 'reset_password'),
    url(r'^upload_photo/?$', 'upload_photo', name = 'upload_photo'),
    url(r'^settings/?$', 'settings', name='settings'),
    url(r'^settings/notifications/?$', 'notifications', name='settings_notifications'),
    url(r'^settings/connect/?$', 'connect', name='settings_connect'),
    url(r'^settings/developer/?$', 'developer', name='settings_developer'),
    url(r'^users/(?P<user_id>\d*)/follow/?$', 'follow', name='follow_user'),
    url(r'^users/(?P<user_id>\d*)/unfollow/?$', 'unfollow', name='unfollow_user'),
    url(r'^users/(?P<user_id>\d*)/followers/?$', 'follower_list', name='user_followers'),
    url(r'^users/(?P<user_id>\d*)/followings/?$', 'following_list', name='user_followings'),
    url(r'^remove/?$', 'remove_user', name='remove_user')
)

urlpatterns += patterns('users.ajax.views',
    url(r'^json/v1/user/fbid_check/?$', 'check_fbid', name = 'check_fbid'),
    url(r'^json/v1/user/fb_login/?$', 'fb_login', name = 'fb_login'),
    url(r'^json/v1/user/fbot_update/?$', 'fbot_update', name = 'fbot_update'),
    url(r'^json/v1/user/update/?$', 'update_user', name = 'update_user'),
    url(r'^json/v1/user/remove/?$', 'remove_user', name = 'remove_user'),
    url(r'^json/v1/user/reset_password/?$', 'reset_password', name = 'reset_password'),
    url(r'^json/v1/user/forgot_password/?$', 'forgot_password', name = 'forgot_password'),
    url(r'^json/v1/user/action/follow/?$', 'follow', name = 'follow'),
)

''' END OF USER URLs '''


''' ISSUE URLs '''
urlpatterns += patterns('issue.views',
    url(r'^issue/(?P<mongo_id>[a-zA-Z0-9\-_].*)/?$', 'old_issue_permalink', name = 'old_issue_permalink'),
    url(r'^issuename/(?P<issuename>[a-zA-Z0-9\-_\ ].*)/?$', 'old_issuename_permalink', name = 'old_issuename_permalink'),
    url(r'^users/(?P<user_id>\d*)/issues/?$', 'followed_issue_list', name='followed_issue_list')
)

''' ISSUE URLs '''


''' ORG URLs '''
urlpatterns += patterns('org.views',
    url(r'^org/categories.js$', 'org_categories', name = 'org_categories'),
    url(r'^org/claim/(?P<org_id>[0-9a-zA-Z\-_].*)/confirm/?$', 'claim_org_confirm', name = 'claim_org_confirm'),
    url(r'^org/claim/(?P<org_id>[0-9a-zA-Z\-_].*)/?$', 'claim_org', name = 'claim_org'),
    url(r'^org/create/?$', 'create_org', name = 'create_org'),
    url(r'^org/(?P<org_id>\d.*)/details/?$', 'details', name='details_org'),
    url(r'^org/(?P<org_id>[0-9a-zA-Z\-_].*)/manage/?$', 'manage_org', {'tab': 'about'}, name='manage_org'),
    url(r'^org/(?P<org_id>[0-9a-zA-Z\-_].*)/manage/connect/?$', 'manage_org', {'tab': 'connect'}, name='manage_org_connect'),
    url(r'^org/(?P<org_id>[0-9a-zA-Z\-_].*)/manage/more/?$', 'manage_org', {'tab': 'more'}, name='manage_org_more'),
    url(r'^org/(?P<mongo_id>[a-zA-Z0-9\-_].*)/?$', 'old_org_permalink', name = 'old_org_permalink'),
    url(r'^orgname/(?P<orgname>[a-zA-Z0-9\-_\ ].*)/?$', 'old_orgname_permalink', name = 'old_orgname_permalink'),
    url(r'^users/(?P<user_id>\d*)/orgs/?$', 'followed_org_list', name='followed_org_list')
)

urlpatterns += patterns('org.ajax.views',
    url(r'^json/v1/org/fetch_centroid/?$', 'fetch_org_by_centroid', name = 'fetch_org_by_centroid'),
    url(r'^json/v1/org/update/?$', 'update_org', name = 'update_org'),
    url(r'^json/v1/org/remove/?$', 'remove_org', name = 'remove_org'),
    url(r'^json/v1/org/flag/?$', 'flag_org', name = 'flag_org'),
    url(r'^json/v1/org/create/?$', 'org_create', name = 'org_create'),
    url(r'^json/v1/org/normalize_facebook_id/?$', 'normalize_facebook_id', name = 'normalize_facebook_id'),

)
''' END OF ORG URLs '''


''' COMMITMENT URLS '''
urlpatterns += patterns('commitment.views',
    url(r'^commitments/create/?$', 'create', name='create_commitment'),
    url(r'^commitments/(?P<commitment_id>\d*)/delete/?$', 'delete', name='delete_commitment'),
    url(r'^orgs/(?P<entity_id>\d*)/commitments/?$', 'list', {'model_name': 'org.Org'}, name='org_commitments'),
    url(r'^issues/(?P<entity_id>\d*)/commitments/?$', 'list', {'model_name': 'issue.Issue'}, name='issue_commitments'),
)

''' ACTION URLS '''
urlpatterns += patterns('action.views',
    url(r'^orgs/(?P<entity_id>\d*)/actions/?$', 'action_list', {'model_name': 'org.Org'}, name='org_action_list'),
    url(r'^issues/(?P<entity_id>\d*)/actions/?$', 'action_list', {'model_name': 'issue.Issue'}, name='issue_action_list'),
)

''' SEARCH URLS '''

urlpatterns += patterns('search.views',
                        url(r'^json/v1/search/onebox/?$', 'autocomplete', name = 'autocomplete'),
                        url(r'^search/?$', 'search_page', name='search_page'),
                        url(r'^json/v1/search/?$', 'ajax_search', name='ajax_search'),
                        url(r'^json/v1/autocomplete/?$', 'ajax_term_complete', name='ajax_term_complete')
                        )

''' MAILER URLS '''

urlpatterns += patterns('mailer.views',
    url(r'^unsubscribe/$', 'unsubscribe', name='unsubscribe'),
    url(r'^email/text/(?P<username>[a-zA-Z0-9\-_\ ].*)/?$', 'jumo_reader', name = 'jumo_reader'),
    url(r'^email/(?P<username>[a-zA-Z0-9\-_\ ].*)/?$', 'jumo_reader', name = 'jumo_reader'),
    #url(r'^notification/(?P<username>[a-zA-Z0-9\-_\ ].*)/?$', 'notification_email', name = 'notification_email'),
)

''' END MAILER URLS '''


''' ADMIN URLS '''
urlpatterns += patterns('',
    (r'^admin/org/report/$', 'org.admin_views.report'),
    (r'^grappelli/', include('grappelli.urls')),
    (r'^admin/', include(admin.site.urls)),
)

if settings.IS_DATAMINE:
    urlpatterns += patterns('miner.views',
                    url(r'^related_searches/?$', 'related_searches', name='related_searches')
                    )

#if settings.DEBUG:
if True:
    urlpatterns += patterns('django.views.static',
    (r'^static/(?P<path>.*)$',
        'serve', {
        'document_root': settings.MEDIA_ROOT,
        'show_indexes': True }),)


handler500 = 'etc.views.error_500'
handler404 = 'etc.views.error_404'

'''
#########################################################################################
### HEY         #########################################################################
################################################## SEE ALL THEM POUND SIGNS? ############
#########################################################################################
############### THAT MEANS THIS IS AN IMPORTANT MSG #####################################
#########################################################################################
################################# SO PAY ATTENTION OK? ##################################
#########################################################################################
####### EVERYTHING WILL BREAK IF THIS ISN'T THE LAST LINE OF CODE IN THIS FILE. #
#########################################################################################
################################## WE COOL? #############################################
#########################################################################################
'''

urlpatterns += patterns('etc.views',
    url(r'^([a-zA-Z0-9\-_].*)/?$', 'clean_url', name = 'entity_url'),
)
