#!/usr/bin/env python
from httplib2 import Http
import md5
from hashlib import sha1,sha256
from base64 import b64encode
from urllib import quote
import json
import time
import random


class VolunteerMatch(object):
    """Volunteer Match API Class"""
    def __init__(self,username,password):
        self.username = username
        self.password = password
        self._authorize()
        self.http = Http()
        self.http.follow_all_redirects = True

    def _authorize(self):
        self._gen_auth_headers()

    def _gen_auth_headers(self):
        # generate the annoying wsse headers
        nonce = self._gen_nonce()
        create_time = self._gen_time()
        digest = self._gen_pass_digest(self.password,create_time,nonce)
        headers = {}
        headers['content-type'] = 'application/json'
        headers['Authorization'] = 'WSSE profile="UsernameToken"'
        headers['X-WSSE'] = 'UsernameToken Username="%s", PasswordDigest="%s", Nonce="%s", Created="%s"' % (self.username, digest, nonce, create_time)
        self.headers = headers

    def hello(self):
        return self._call_volmatch("helloWorld", {'name' : 'John' })

    def get_key_status(self):
        return self._call_volmatch('getKeyStatus',{})

    def get_metadata():
        # getMetaData
        pass

    def get_service_status():
        #getServiceStatus
        pass

    def search_volops(self,**kwargs):
        if kwargs.has_key('virtual') or kwargs.has_key('location'):
            return self._call_volmatch("searchOpportunities", kwargs)
        else:
            raise Exception, "Requires either virtual or location"
        #searchOpportunities

    def search_orgs(self,**kwargs):
        return self._call_volmatch('searchOrganizations',kwargs)
        #searchOrganizations

    def _gen_nonce(self):
        # lifted from httplib2
        dig = sha1("%s:%s" % (time.ctime(), ["0123456789"[random.randrange(0, 9)] for i in range(20)])).hexdigest()
        return dig[:20]

    def _gen_time(self):
        return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime())

    def _gen_pass_digest(self,api_key,pass_time,pass_nonce):
        key = pass_nonce + pass_time + api_key
        return b64encode(sha256(key).digest())

    def _call_volmatch(self,call, payload):
        js = json.dumps(payload,separators=(',',':'))
        js = quote(js)
        url = 'http://www.volunteermatch.org/api/call?action=%s&query=%s' % (call,js)
        print "hitting url %s" % url
        try:
            (resp,content) = self.http.request(url,headers=self.headers)
            returned_data = json.loads(content)
            if resp.status != 200:
                raise
            return returned_data
        except Exception:
            print Exception
            return None

if __name__ == '__main__':
    username = ""
    password = ""
    vm = VolunteerMatch(username,password)
    print vm.search_volops(orgNames=['Red Cross'],virtual=True,pageNumber=1)
    print vm.get_key_status()
    print vm.hello()
    print vm.search_orgs(location='New York')
    print vm.search_orgs(
        location="94108",
        nbOfResults= 10,
        pageNumber= 1,
        fieldsToDisplay=[ "name", "location" ],
        names=[ "red cross" ]
        )
    print vm.headers
