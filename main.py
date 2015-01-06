# Web Server Gateway Interface (WSGI)

from google.appengine.api import users
import webapp2
import json
from google.appengine.api import urlfetch
from google.appengine.ext import ndb

gKey = 'AIzaSyAFUzCTsEsH3V7naec9V50HxbSYkKFSKLw'
BASE_URL_GOOGLE_PLACE = "https://maps.googleapis.com/maps/api/place"
BASE_URL_GAE = ""
USER_AGENT = "RESTAURANT APP TESTING Agent"
REFERRER = ""


class Entry(ndb.Model):
    placeId = ndb.StringProperty()
    start = ndb.IntegerProperty()
    end = ndb.IntegerProperty()
    duration = ndb.IntegerProperty()
    dataTimeUpdated = ndb.DateTimeProperty(auto_now=True)
    dateTimeCreated = ndb.DateTimeProperty(auto_now_add=True)

    def find(self, _placeId):
        return self.query(Entry.placeId == _placeId).fetch()

    def add(self, _placeId, _start, _end, _duration):
        obj = Entry(placeId=_placeId,
                    start=int(_start),
                    end=int(_end),
                    duration=int(_duration))
        obj.put()


class Access(ndb.Model):
    placeId = ndb.StringProperty()
    count = ndb.IntegerProperty()
    dataTimeUpdated = ndb.DateTimeProperty(auto_now=True)
    dateTimeCreated = ndb.DateTimeProperty(auto_now_add=True)

    def find(self, _placeId):
        return self.query(Access.placeId==_placeId)

    def add(self, _placeId):
        ret = self.query(Access.placeId==_placeId).get()
        if ret is not None:
            ret.count += 1
            ret.put()
        else:
            obj = Access(placeId=_placeId,
                                 count=1)
            obj.put()



class LandingHandler(webapp2.RequestHandler):
    def get(self):  # Get Request
        self.response.headers['Content-type'] = 'text/plain'
        self.response.write((self.request.referrer or "null")+"/n")
        self.response.write((self.request.user_agent or "null")+"/n")
        self.response.write((self.request._headers or "null")+"/n")
        self.response.write((self.request.content_length or "null")+"/n")
        self.response.write((self.request.remote_addr or "null")+"/n")


class SearchHandler(webapp2.RequestHandler):
    def get(self):  # Get Request
        loc = self.request.get('location','',False)
        rad = self.request.get('radius','',False)
        typ = self.request.get('types','',False)
        pKey = self.request.get('p','',False)
        if pKey == 'private_key' and (loc is not "" and rad is not "" and typ is not ""):
            self.response.headers['Content-type'] = 'application/json'
            url = BASE_URL_GOOGLE_PLACE+'/nearbysearch/json?'
            url += 'key='+gKey+'&'
            url += 'location='+loc+'&'
            url += 'radius='+rad+'&'
            url += 'types='+typ
            ret = urlfetch.fetch(url)
            self.response.write(self.data_modification(ret.content))
            #self.response.write(ret.content)

    def data_modification(self, content):
        layer1 = json.loads(content)
        layer2 = layer1["results"]
        print len(layer2)
        for i in range(0,len(layer2)):
            _place_id = layer2[i]["place_id"]
            if _place_id is not None or _place_id is not "":
                print _place_id
                obj = Entry()
                ret = obj.find(_place_id)
                if ret is not None and len(ret) is not 0:
                    sum = 0
                    print ret
                    for r in ret:
                        sum += r.duration
                    sum = sum/len(ret)
                else:
                    sum = 0
            else:
                print "else "+_place_id
            print layer2[i]
            layer2[i]["waiting"] = sum

        return json.dumps(layer1)


class DetailsHandler(webapp2.RequestHandler):
    def get(self):  # Get Request
        id = self.request.get('placeid','',False)
        pKey = self.request.get('p','',False)
        if pKey == 'private_key' and id is not "":
            url = BASE_URL_GOOGLE_PLACE+'/details/json?'
            url += 'key='+gKey+'&'
            url += 'placeid='+id
            ret = urlfetch.fetch(url)
            self.response.headers['Content-type'] = 'application/json'
            self.data_handling(ret.content)
            self.response.write(ret.content)

    def data_handling(self,content):
        layer1 = json.loads(content)
        layer2 = layer1["result"]
        place_id = layer2["place_id"]
        obj = Access()
        obj.add(place_id)


class PutDataHandler(webapp2.RequestHandler):
    def get(self):  # Get Request
        _placeid = self.request.get('placeid','',False)
        _start = self.request.get('start','',False)
        _end = self.request.get('end','',False)
        _duration = self.request.get('duration','',False)
        _p = self.request.get('p','',False)
        if _p == 'private_key' and _placeid is not '' and _duration is not '' and _start is not '' and _end is not '':
            obj = Entry()
            obj.add(_placeid,_start,_end,_duration)
            self.response.headers['Content-type'] = 'application/json'
            content = {'placeid':_placeid,
                       'start':_start,
                       'end':_end,
                       'duration':_duration,
                        'status': 'OK'}
            content = json.dumps(content)
            self.response.write(content)

class GetDataHandler(webapp2.RequestHandler):
    def get(self):  # Get Request
        _placeid = self.request.get('placeid','',False)
        _p = self.request.get('p','',False)
        if _p == 'private_key' and _placeid is not '':
            obj = Entry()
            ret = obj.find(_placeid)
            sum = 0
            cnt = 0
            print ret
            for r in ret:
                cnt += 1
                sum += r.duration
            if cnt == 0:
                cnt = 1
            sum = sum/cnt

            self.response.headers['Content-type'] = 'application/json'
            content = {'place_id': _placeid,'average': sum, 'status': 'OK'}
            content = json.dumps(content)
            self.response.write(content)

landingApp = webapp2.WSGIApplication([
    ('/', LandingHandler)
], debug=True) # tell webapp2 to print stack traces to the broswer output if there s an error.

searchApp = webapp2.WSGIApplication([
    ('/search', SearchHandler)
], debug=True) # tell webapp2 to print stack traces to the broswer output if there s an error.

detailsApp = webapp2.WSGIApplication([
    ('/details', DetailsHandler)
], debug=True) # tell webapp2 to print stack traces to the broswer output if there s an error.

putDataApp = webapp2.WSGIApplication([
    ('/putData', PutDataHandler)
], debug=True) # tell webapp2 to print stack traces to the broswer output if there s an error.

getDataApp = webapp2.WSGIApplication([
    ('/getData', GetDataHandler)
], debug=True) # tell webapp2 to print stack traces to the broswer output if there s an error.
