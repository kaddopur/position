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
import cgi
import os
import simplejson
from dbmodel import *
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import images

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
        if map:
            id = map.map_id
        else:
            id = 0
            
        Points = Point.all().fetch(5)
        points_data = zip([point.x for point in Points], [point.y for point in Points], [point.point_id for point in Points])
        #print kkk
        template_values = {
            'logout_url': logout_url,
            'map': map,
            'points_data' : simplejson.dumps(points_data),
            'all_points': Point.all().filter('map_id = ', id).fetch(5)
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
        
        
        name_list = [u'主臥室', u'書房', u'客廳'];
        desc_list = [u'主臥室的規劃，是整個設計中非常重要的一環。對空間與功能上的要求也必須詳加考慮，才不會造成日後生活上的不便。', 
                u'一個規劃完善的書房，可以說是家裡的世外桃源、避風港。在這裡，你可以悠閒地看看書、聽聽音樂，即便只是望著窗外的景色發呆，都是一件十分過癮的事。',
                u'客廳設計的風格定位裝修之前首先就要確定自己想要的風格'];
                
        for i in range(3):
            point = Point( map_id = map.map_id , point_id = i+1)
            point.title = name_list[i]
            point.description = desc_list[i]
            point.put()
        self.redirect('/')
        
        
class QRAll(webapp.RequestHandler):
    def get(self):
        map = db.get(self.request.get("key"))
        
        query = Point.all()
        query.filter('map_id =', map.map_id)
        query.order('point_id')
        results = query.fetch(1000)
        
        template_values = {
            'map': map,
            'points': results
        }
            
        path = os.path.join(os.path.dirname(__file__), 'qrcode_all.html')
        self.response.out.write(template.render(path, template_values))

class AddPoint(webapp.RequestHandler):
    def post(self):
        map = db.get(self.request.get("key"))
            
        query = Point.all()
        query.filter('map_id =', map.map_id)
        query.order('-point_id')
        
        largest_point = query.get()
        
        point = Point()
        
        if largest_point:
            point.point_id = largest_point.point_id + 1
        else:
            point.point_id = 1
        point.title = ("new point")
        point.map_id = map.map_id
        point.x = int(self.request.get("x"))
        point.y = int(self.request.get("y"))
        print point.point_id
        point.put()
        self.redirect('/')
        
        
application = webapp.WSGIApplication([('/', MainPage),
                                      ('/upload_map', UploadMap),
                                      ('/map_image', MapImage),
                                      ('/drop_map', DropMap),
                                      ('/update_map', UpdateMap),
                                      ('/qr_all', QRAll),
                                      ('/add_point', AddPoint)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
