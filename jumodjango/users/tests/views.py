from django.core import mail
from etc.constants import ACCOUNT_COOKIE_SALT, ACCOUNT_COOKIE
from etc.tests import ViewsBaseTestCase, BASE_TEST_USER, BASE_TEST_PASS, NON_FB_USER
from django.core.urlresolvers import reverse


VALID_CREATE_USER_FORM_DATA = dict(first_name="Doktr", last_name="Nepharious", gender='male', password='tester01', email='notreal@ffffake.com',
                                   birth_year='1909', fbid='',
                                   fb_access_token='',
                                   friends='174800237,538431833,671896922,1626665502,100001197186897,100001739003909',
                                   location='New York, United States (Town)',
                                   location_data='{"name":"New York","latitude":"40.714550","longitude":"-74.007118","postal_code":"","address":"","type":"Town","raw_geodata":{"lang":"en-US","uri":"http://where.yahooapis.com/v1/place/2459115","woeid":"2459115","placeTypeName":{"code":"7","content":"Town"},"name":"New York","country":{"code":"US","type":"Country","content":"United States"},"admin1":{"code":"US-NY","type":"State","content":"New York"},"admin2":null,"admin3":null,"locality1":{"type":"Town","content":"New York"},"locality2":null,"postal":null,"centroid":{"latitude":"40.714550","longitude":"-74.007118"},"boundingBox":{"southWest":{"latitude":"40.495682","longitude":"-74.255653"},"northEast":{"latitude":"40.917622","longitude":"-73.689484"}},"areaRank":"4","popRank":"13"},"locality":"New York","region":"New York","country_name":"United States"}')

INVALID_CREATE_USER_FORM_DATA = dict()


class PageTests(ViewsBaseTestCase):

    def test_index(self):
        index_url = '/'
        index_template = 'etc/home.html'
        index_template_loggedin = 'user/home.html'

        #Logged Out Test
        self.basic_200_test(index_url, index_template)
        #Logged In Test
        self.login()
        self.basic_200_test(index_url, index_template_loggedin)


    def test_login(self):
        """More thorough version of what's being done in the base class"""
        #MAKE SURE COOKIES DON'T EXIST
        self.assertEqual(self.client.cookies.get(ACCOUNT_COOKIE, None), None)
        self.assertEqual(self.client.cookies.get(ACCOUNT_COOKIE_SALT, None), None)

        redirect_to = "/"
        response = self.client.post("/login", data={"username":BASE_TEST_USER, "password":BASE_TEST_PASS, "redirect_to":redirect_to})
        self.assertRedirects(response, redirect_to)
        #Make Sure Cookies Are There And Have Value
        self.assertNotEqual(self.client.cookies.get(ACCOUNT_COOKIE, None), None)
        self.assertNotEqual(self.client.cookies.get(ACCOUNT_COOKIE_SALT, None), None)
        self.assertNotEqual(self.client.cookies[ACCOUNT_COOKIE].value, "")
        self.assertNotEqual(self.client.cookies[ACCOUNT_COOKIE_SALT].value, "")

        #Make sure a non-fb user can log in as well.
        self.logout()
        response = self.client.post("/login", data={"username":NON_FB_USER['email'], "password":NON_FB_USER['pwd'], "redirect_to":redirect_to})
        self.assertRedirects(response, redirect_to)


    def test_logout(self):
        self.login()

        #Make Sure Cookies Are There And Have Value
        self.assertNotEqual(self.client.cookies.get(ACCOUNT_COOKIE, None), None)
        self.assertNotEqual(self.client.cookies.get(ACCOUNT_COOKIE_SALT, None), None)
        self.assertNotEqual(self.client.cookies[ACCOUNT_COOKIE].value, "")
        self.assertNotEqual(self.client.cookies[ACCOUNT_COOKIE_SALT].value, "")

        #Make Sure Cookies Are Gone
        self.client.get('/logout')
        self.assertEqual(self.client.cookies[ACCOUNT_COOKIE].value, "")
        self.assertEqual(self.client.cookies[ACCOUNT_COOKIE_SALT].value, "")

    def test_setup(self):
        setup_url = "/setup"
        setup_success_url = "/"
        setup_template = "user/setup.html"

        #Test Page Loads
        self.basic_200_test(setup_url, setup_template)
        #Test Invalid Post
        self.form_fails_test(setup_url, INVALID_CREATE_USER_FORM_DATA, "create_form", setup_template)
        #Test Valid Post (View Redirects so we don't do normal test here.)
        response = self.client.post(setup_url, VALID_CREATE_USER_FORM_DATA)
        self.assertRedirects(response, setup_success_url)

    def test_discover(self):
        discover_url = "/discover"
        discover_template = "user/discover.html"

        #Not logged in should redirect!
        self.login_redirect_test(discover_url)

        #Logged in should be good.
        self.login()
        self.basic_200_test(discover_url, discover_template)

    def test_settings(self):
        settings_url = reverse('settings')
        settings_template = "user/settings.html"

        #Not logged in should redirect!
        self.login_redirect_test(settings_url)

        #Logged in should be good.
        self.login()
        self.basic_200_test(settings_url, settings_template)

    def test_forgot_password(self):
        url = "/forgot_password"
        template = "user/forgot_password.html"
        template_success = "user/forgot_password_confirm.html"

        self.basic_200_test(url, template)

        #Failed Attempt Should Use the Same Template
        response = self.client.post(url, dict(email="adfasdfasdf"))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
        self.assertTemplateUsed(response, template)

        #Succesful Attempt Should Use the Success Template
        response = self.client.post(url, dict(email="brennan@jumo.com"))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
        self.assertTemplateUsed(response, template_success)

        self.assertEquals(len(mail.outbox), 1)
