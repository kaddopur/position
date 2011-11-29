#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
import cgi
import os
import simplejson
from dbmodel import *
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import images
import urllib
import logging  

logging.basicConfig(filename='/tmp/app.log', level=logging.INFO,  
                    format='%(asctime)s %(levelname)s %(message)s')  
logging.info('run')  

_DEBUG = True

class BaseRequestHandler(webapp.RequestHandler):
  """Base request handler extends webapp.Request handler

     It defines the generate method, which renders a Django template
     in response to a web request
  """

  def generate(self, template_name, template_values):
    """Generate takes renders and HTML template along with values
       passed to that template

       Args:
         template_name: A string that represents the name of the HTML template
         template_values: A dictionary that associates objects with a string
           assigned to that object to call in the HTML template.  The defualt
           is an empty dictionary.
    """
    # We check if there is a current user and generate a login or logout URL
    user = users.get_current_user()

    if not user:
        self.redirect(users.create_login_url(self.request.uri))
        
    
    # after log in
    logout_url = users.create_logout_url(self.request.uri)
    
    map_results = Map.all().filter('author =', user).order('date').fetch(1000)
    user_maps = [ (str(map.key()), map.title) for map in map_results]
    map = Map.all().filter('author =', user).order('-date').get()
    point_results = []
    point_data = []
    point_titles = []
    point_descriptions = []
    point_photos = []
    if map:
        point_results = Point.all().filter('map_id =', map.map_id).order('title').fetch(1000)
        if point_results:
            point_data = [(point.x, point.y, point.point_id) for point in point_results]
            point_titles = [(point.title) for point in point_results]
            point_descriptions = [(point.description) for point in point_results]
            point_photos = [(point.photo_key) for point in point_results]
        
    values = {
        'user' : user,
        'logout_url': logout_url,
        'map': map,
        'user_maps' : simplejson.dumps(user_maps),
        'point_data': simplejson.dumps(point_data),
        'point_titles': simplejson.dumps(point_titles),
        'point_descriptions': simplejson.dumps(point_descriptions),
        'points': point_results,
        'point_photos': simplejson.dumps(point_photos),
    }
    values.update(template_values)
    
    # Construct the path to the template
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, template_name)

    # Respond to the request by rendering the template
    return template.render(path, values, debug=_DEBUG)

class MainPage(BaseRequestHandler):
    def get(self):
        
        self.response.out.write( self.generate('index.html',{}))
        
class UploadMap(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
     
        largest_map = Map.all().order('-map_id').get()
        
        map = Map(author=user, map_id=1)
        if largest_map:
            map.map_id = largest_map.map_id + 1
            
        map.map_ver = 1
        map.title = u'地圖'+ str(map.map_id)
        img = self.request.get("img")
        map.file = db.Blob(str(img))
        if (images.Image(image_data=map.file).width < 700) or (images.Image(image_data=map.file).height < 400):
            template_values = {
                'success': "false",
                'message': "ERROR: Image must be at least 700px X 500px",
                'map_key': "",
            }
            self.response.clear()
            self.response.out.write(simplejson.dumps(template_values))
        else:
            map.put()
            map_results = Map.all().filter('author =', user).order('date').fetch(1000)
            user_maps = [ (str(map.key()), map.title) for map in map_results]
            map = Map.all().filter('author =', user).order('-date').get()
            template_values = {
                'success': "true",
                'message': "successful upload map",
                'map_key': str(map.key()),
                'map_title': map.title,
                'user_maps' : user_maps,
            }
            self.response.clear()
            self.response.out.write(simplejson.dumps(template_values))

class UploadPhoto(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        map = db.get(self.request.get("map_key"))
        point_id = self.request.get('point_id')
        
        query = PointPhoto.all()
        query.filter('map_id =', map.map_id).filter('point_id =', point_id)
        db.delete(query)
        
        photo = PointPhoto()
        photo.map_id = map.map_id
        photo.point_id = int(self.request.get('point_id'))
        img = images.resize(self.request.get('files[]'), 240, 120)
        photo.file = db.Blob(str(img))
        photo.title = self.request.get("point_id")
        photo.put()
        template_values = {
            'success': "true",
            'message': "successful upload photo",
            'photo_key': str(photo.key()),
        }
        self.response.clear()
        self.response.out.write(simplejson.dumps(template_values))

        
class MapImage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        map = db.get(self.request.get("key"))
        
        if map.file:
            self.response.headers['Content-Type'] = "image"
            self.response.out.write(map.file)
        else:
            self.response.out.write("No image")
            
class PointPhotoImage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        photo = db.get(self.request.get("key"))
        
        if photo.file:
            self.response.headers['Content-Type'] = "image"
            self.response.out.write(photo.file)
        else:
            self.response.out.write("No image")
                        
class DropMap(BaseRequestHandler):
    def post(self):
        map = db.get(self.request.get("key"))
        user = users.get_current_user()
        #delete all points related to this map
        query = Point.all()
        query.filter('map_id =', map.map_id)
        db.delete(query)
        
        #delete all Photos related to this map
        query2 = PointPhoto.all()
        query2.filter('map_id =', map.map_id)
        db.delete(query2)
        
        #delete this map
        db.delete(map)
        map_results = Map.all().filter('author =', user).order('date').fetch(1000)
        user_maps = [ (str(map.key()), map.title) for map in map_results]
        template_values = {
            'map': None,
            'user_maps' : user_maps,
        }
        self.response.clear()
        self.response.out.write( simplejson.dumps(template_values))

        
class UpdateMap(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        map = db.get(self.request.get("key"))
        map.title = self.request.get("title")
        map.map_ver = map.map_ver + 1
        map.put()
        map_results = Map.all().filter('author =', user).order('date').fetch(1000)
        user_maps = [ (str(map.key()), map.title) for map in map_results]
        template_values = {
            'user_maps' : user_maps,
        }
        self.response.clear()
        self.response.out.write( simplejson.dumps(template_values))

        
        
class QRAll(webapp.RequestHandler):
    def get(self):
        map = db.get(self.request.get("key"))
        
        query = Point.all()
        query.filter('map_id =', map.map_id)
        query.order('title')
        points = query.fetch(1000)
        
        urls = [ urllib.quote('http://indoorposition.appspot.com/show?mapID=%d&mapVer=%d&pointID=%d&title=' % (map.map_id, map.map_ver, point.point_id)) + point.title for point in points]
        results = zip(points, urls)
        
        template_values = {
            'map': map,
            'results': results
        }
            
        path = os.path.join(os.path.dirname(__file__), 'qrcode_all.html')
        self.response.out.write(template.render(path, template_values))

class QRSingle(webapp.RequestHandler):
    def get(self):
        map = db.get(self.request.get('key'))
        
        query = Point.all()
        query.filter('map_id =', map.map_id).filter('point_id =', int(self.request.get('pointID')))
        point = query.get()
        
        targetURL = urllib.quote('http://indoorposition.appspot.com/show?mapID=%d&mapVer=%d&pointID=%d&title=' % (map.map_id, map.map_ver, point.point_id)) + point.title
        template_values = {
            'url': targetURL
        }
        
        path = os.path.join(os.path.dirname(__file__), 'qrcode_single.html')
        self.response.out.write(template.render(path, template_values))
        
        
class ShowJson(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'

        if self.request.get('from') != 'client':
            self.response.headers['Content-Type'] = 'text/html'
            self.response.out.write('<body charset=\'utf-8\'>')
            self.response.out.write('請使用專用使用者端軟體<p><a href=\'http://dl.dropbox.com/u/871055/posClient.apk\'>下載</a>')
            self.response.out.write('</body>')
            return

        query = Map.all()
        query.filter('map_id =', int(self.request.get('mapID')))
        query.filter('map_ver =', int(self.request.get('mapVer')))
        map = query.get()

        if map:
            point_result = Point.all().filter('map_id =', int(self.request.get('mapID'))).fetch(1000)
            points = []
            for res in point_result:
				photoUrl = ""
				if res.photo_key != None:
					photoUrl = "http://indoorposition.appspot.com/point_photo?key=%s" % res.photo_key
				points.append({"pointID": res.point_id,
                               "title": res.title,
                               "description": res.description,
                               "coord": {"x": res.x, "y": res.y},
                               "photo": photoUrl})

            result = {"mapID": map.map_id,
                       "mapVer": map.map_ver,
                      "title": map.title,
                      "map": "http://indoorposition.appspot.com/map_image?key=%s" % map.key(),
                      "points": points}
            self.response.out.write(simplejson.dumps(result))
        else:
            self.error(404)
            
class RPCHandler(webapp.RequestHandler):
  """ Allows the functions defined in the RPCMethods class to be RPCed."""
  def __init__(self):
    webapp.RequestHandler.__init__(self)
    self.methods = RPCMethods()
 
  def get(self):
    func = None
   
    action = self.request.get('action')
    if action:
        if action[0] == '_':
            self.error(403) # access denied
            return
        else:
            func = getattr(self.methods, action, None)
   
    if not func:
        self.error(405) # file not found
        return
        
    args = ()
    while True:
        key = 'arg%d' % len(args)
        val = self.request.get(key)
        if val:
            args += (simplejson.loads(val),)
        else:
            break
    result = func(*args)
    
    self.response.out.write(simplejson.dumps(result))


class RPCMethods:
    """ Defines the methods that can be RPCed.
    NOTE: Do not allow remote callers access to private/protected "_*" methods.
    """
    #private method __template
    def __template(self, values, map_key):
        # prepare return data
        user = users.get_current_user()
        if not user:
            self.error(404)
        map = db.get(map_key)
        point_results = []
        point_data = []
        point_titles = []
        point_descriptions = []
        point_photos = []
        map_title = ""
        if map:
            map_title = map.title
            point_results = Point.all().filter('map_id =', map.map_id).order('title').fetch(1000)
            if point_results:
                point_data = [(point.x, point.y, point.point_id) for point in point_results]
                point_titles = [(point.title) for point in point_results]
                point_descriptions = [(point.description) for point in point_results]
                point_photos = [(point.photo_key) for point in point_results]
                
            
        template_values = {
            'point_id': 0,
            'point_data': point_data,
            'point_titles': point_titles,
            'point_descriptions': point_descriptions,
            'point_photos': point_photos,
            'map_title': map_title,
        }
        template_values.update(values)
        return template_values
    

        
    
    def addPointAjax(self, *args):
        
        #add new point into database
        mapkey = args[0]
        x = args[1]
        y = args[2]
        
        map = db.get(mapkey)
        map.map_ver = map.map_ver + 1

        query = Point.all()
        query.filter('map_id =', map.map_id)
        query.order('-point_id')
        largest_point = query.get()
        
        point_id = 1
        point = Point(map_id=map.map_id, point_id=1)
        if largest_point:
            point_id = largest_point.point_id + 1
            point.point_id = largest_point.point_id + 1
        point.title = (u'定位點'+ str( point_id))
        point.x = int(x)
        point.y = int(y)
        point.description = "no description"
        point.put()
        map.put()       
        
        values = {
            'point_id': point_id,
        }
        
        return self.__template( values, mapkey)
    
    def changeMapAjax(self, *args):
        mapkey = args[0]
        values = {
            'map_key': mapkey,
        }
        return self.__template( values, mapkey)
    
    def updatePointAjax(self, *args):
        mapkey = args[0]
        point_id = args[1]
        title = args[2]
        desc = args[3]
        photo_key = args[4]

        map = db.get(mapkey)
        map.map_ver = map.map_ver + 1
        
        point = Point.all().filter('map_id = ', map.map_id).filter('point_id =', int(point_id)).get()
        point.title = title
        point.description = desc
        point.photo_key = photo_key
        point.put()
        map.put()
        
        values = {
            'point_id': point_id,
        }
        
        return self.__template( values, mapkey)
        
    def deletePointAjax(self, *args):
        mapkey = args[0]
        point_id = args[1]
        
        map = db.get(mapkey)
        map.map_ver = map.map_ver + 1
        
        point = Point.all().filter('map_id = ', map.map_id).filter('point_id =', int(point_id)).get()
        point.delete()
        map.put()
        
        values = {
            'point_id': 0,
        }
        
        return self.__template( values, mapkey)
     
  
    
application = webapp.WSGIApplication([('/', MainPage),
                                      ('/upload_map', UploadMap),
                                      ('/map_image', MapImage),
                                      ('/point_photo', PointPhotoImage),
                                      ('/drop_map', DropMap),
                                      ('/update_map', UpdateMap),
                                      ('/qr_all', QRAll),
                                      ('/qr_single', QRSingle),
                                      ('/show', ShowJson),
                                      ('/upload_photo', UploadPhoto),
                                      ('/rpc', RPCHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
