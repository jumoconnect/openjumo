from etc.tests import ViewsBaseTestCase, BASIC_USER
from org.models import Org
from django.core.urlresolvers import reverse

"""FOR LATER

urlpatterns += patterns('org.views',
    url(r'^donate/(?P<handle>[0-9a-zA-Z\-_].*)/?$', 'donate', name = 'donate'),
    url(r'^org/(?P<mongo_id>[a-zA-Z0-9\-_].*)/?$', 'old_org_permalink', name = 'old_org_permalink'),
    url(r'^orgname/(?P<orgname>[a-zA-Z0-9\-_\ ].*)/?$', 'old_orgname_permalink', name = 'old_orgname_permalink'),
)
"""


class PageTests(ViewsBaseTestCase):
    
    def test_create_org(self):
        url = reverse('create_org')
        template = 'org/create.html'

        #Redirect if not logged in
        self.login_redirect_test(url, True)

        #Show page after login
        self.basic_200_test(url, template)


    #This is in the process of getting converted to a django form.
    #def test_manage_org(self):
    #    org_id = Org.objects.all()[0].id
    #
    #    good_url = reverse('manage_org', kwargs={'org_id':org_id})
    #    template = 'common/entity/manage.html'
    #    bad_url = reverse('manage_org', kwargs={'org_id':-1})
    #
    #    self.login_redirect_test(good_url)
    #
    #    #Raise 404 on invalid org id
    #    self.login()
    #    self.basic_404_test(bad_url)
    #
    #    #Should render correctly since we're logged in as staff
    #    self.basic_200_test(good_url, template)
    #
    #    #Raise 404 since we're a basic user
    #    self.logout()
    #    self.login(BASIC_USER)
    #    self.basic_404_test(good_url)

    def test_donate(self):
        handle = Org.objects.all()[0].handle
        pass


    def test_claim_org(self):
        org_id = Org.objects.all()[0].id
        good_url = "/org/claim/%s" % org_id
        good_template = 'org/claim.html'
        bad_url = "/org/claim/-1"

        #Not logged in should redirect
        self.login_redirect_test(good_url)

        #Should work after logging in
        self.login()
        self.basic_200_test(good_url, good_template)

        #404 if Org doesn't exist
        self.basic_404_test(bad_url)

    def test_claim_org_confirm(self):
        org_id = Org.objects.filter()[0].id
        org_url = reverse('claim_org_confirm', kwargs={'org_id':org_id})
        bad_url = reverse('claim_org_confirm', kwargs={'org_id':-1})

        template = 'org/claimed.html'

        #Requires logged in user
        self.login_redirect_test(org_url, True)

        #Raise 404 on invalid org
        self.basic_404_test(bad_url)
        self.basic_200_test(org_url, template)
