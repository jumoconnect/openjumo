from data.gen_fixtures import BASIC_USER as FIXTURE_USER, NON_FB_USER as NON_FB_FIXTURE_USER
from django.core.urlresolvers import reverse
from django.test import TestCase

STAFF_USER = {'email':'nick@jumo.com', 'pwd':'tester01'}
BASIC_USER = {'email':FIXTURE_USER['email'], 'pwd':FIXTURE_USER['password']}
NON_FB_USER = {'email':NON_FB_FIXTURE_USER['email'], 'pwd':NON_FB_FIXTURE_USER['password']}
BASE_TEST_USER = 'nick@jumo.com'
BASE_TEST_PASS = 'tester01'

class JumoBaseTestCase(TestCase):
    pass

class ViewsBaseTestCase(JumoBaseTestCase):
    def login(self, user=STAFF_USER):
        redirect_to = "/"
        response = self.client.post("/login", data={"username":user['email'], "password":user['pwd'], "redirect_to":redirect_to})
        self.assertRedirects(response, redirect_to)

    def logout(self):
        redirect_to = reverse('index')
        response = self.client.get("/logout")
        self.assertRedirects(response, redirect_to)

    def basic_200_test(self, end_point, expected_template):
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
        self.assertTemplateUsed(response, expected_template)

    def basic_404_test(self, end_point):
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/error.html')

    def basic_500_test(self, end_point):
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, 'errors/error.html')

    def login_redirect_test(self, end_point, login=False):
        response = self.client.get(end_point)
        self.assertRedirects(response, "/login?redirect_to=%s" % end_point)
        if login: self.login()

    def form_succeeds_test(self, end_point, post_data, expected_template):
        response = self.client.post(end_point, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
        self.assertTemplateUsed(response, expected_template)

    def form_fails_test(self, end_point, post_data, form_name, expected_template):
        #NOTE: assertFormError was dumb.
        #Also not sure if I like the fom_name thing...that was stole from django example.
        response = self.client.post(end_point, post_data)
        if form_name not in response.context:
            self.fail("The form '%s' was not used to render the response for %s" % (form_name, end_point))
        self.assertFalse(response.context[form_name].is_valid())
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 0)
        self.assertTemplateUsed(response, expected_template)
