#!/usr/bin/env python
#
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
import cgi
import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.api import images

class Map(db.Model):
    author = db.UserProperty()
    map_id = db.IntegerProperty()
    map_ver = db.IntegerProperty()
    title = db.TextProperty()
    file = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    
class Point(db.Model):
    map_id = db.IntegerProperty()
    point_id = db.IntegerProperty()
    title = db.TextProperty()
    description = db.TextProperty()
    x = db.IntegerProperty()
    y = db.IntegerProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    
class PointPhoto(db.Model):
    map_id = db.IntegerProperty()
    point_id = db.IntegerProperty()
    file = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
    def get(self):
        # build namespace
        query = Map.all()
        if query.count() < 1:
            map = Map()
            map.map_id = 0
            map.put()
        
        query = Point.all()
        if query.count() < 1:
            point = Point()
            point.map_id = 0
            point.point_id = 0
            point.put()
            
        query = PointPhoto.all()
        if query.count() < 1:
            point_photo = PointPhoto()
            point_photo.map_id = 0
            point_photo.point_id = 0
            point_photo.put()
            
            
        
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        # after log in
        logout_url = users.create_logout_url(self.request.uri)
        
        query = Map.all()
        query.filter('author =', user)
        query.order('-date')
        map = query.get()
        
        template_values = {
            'logout_url': logout_url,
            'map': map
        }
            
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

        
class UploadMap(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        
        query = Map.all()
        query.order('-map_id')
        largest_map = query.get()
        
        map = Map()
        map.author = user
        
        if largest_map:
            map.map_id = query.get().map_id + 1
        else:
            map.map_id = 1
        map.map_ver = 1
        map.title = ''
        map.file = db.Blob(self.request.get("img"))
        map.put()
        
        self.redirect('/')
        
class MapImage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        map = db.get(self.request.get("key"))
        
        if map.file:
            self.response.headers['Content-Type'] = "image"
            self.response.out.write(map.file)
        else:
            self.response.out.write("No image")
            
            
class DropMap(webapp.RequestHandler):
    def get(self):
        map = db.get(self.request.get("key"))
        
        #delete all points related to this map
        query = Point.all()
        query.filter('map_id =', map.map_id)
        results = query.fetch(1000)
        db.delete(results)
        
        #delete this map
        db.delete(map)
        
        self.redirect('/')
        
class UpdateMap(webapp.RequestHandler):
    def post(self):
        map = db.get(self.request.get("key"))
        map.title = self.request.get("title")
        map.put()
        self.redirect('/')

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/upload_map', UploadMap),
                                      ('/map_image', MapImage),
                                      ('/drop_map', DropMap),
                                      ('/update_map', UpdateMap)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
