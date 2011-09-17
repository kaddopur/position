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
import urllib

class MainPage(webapp.RequestHandler):
    def get(self):
        query = Point.all()
        if query.count() < 1:
            point = Point(map_id=0, point_id=0)
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
        
        map = Map.all().filter('author =', user).order('-date').get()
        point_results = []
        point_data = []
        point_titles = []
        point_descriptions = []
        if map:
            point_results = Point.all().filter('map_id =', map.map_id).order('title').fetch(1000)
            if point_results:
                point_data = [(point.x, point.y, point.point_id) for point in point_results]
                point_titles = [(point.title) for point in point_results]
                point_descriptions = [(point.description) for point in point_results]
            
        template_values = {
            'logout_url': logout_url,
            'map': map,
            'point_data': simplejson.dumps(point_data),
            'point_titles': simplejson.dumps(point_titles),
            'point_descriptions': simplejson.dumps(point_descriptions),
            'points': point_results
        }
        
            
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

        
class UploadMap(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
     
        largest_map = Map.all().order('-map_id').get()
        
        map = Map(author=user, map_id=1)
        if largest_map:
            map.map_id = largest_map.map_id + 1
            
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
    def post(self):
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

class AddPoint(webapp.RequestHandler):
    def post(self):
        map = db.get(self.request.get("key"))
        
        query = Point.all()
        query.filter('map_id =', map.map_id)
        query.order('-point_id')
        largest_point = query.get()
        
        point = Point(map_id=map.map_id, point_id=1)
        
        if largest_point:
            point.point_id = largest_point.point_id + 1
        point.title = (u'新定位點')
        point.x = int(self.request.get("x"))
        point.y = int(self.request.get("y"))
        point.put()
        
        self.redirect('/?pointID='+str(point.point_id))
        
class UpdatePoint(webapp.RequestHandler):
    def post(self):
        map = db.get(self.request.get("key"))
        
        point = Point.all().filter('map_id = ', map.map_id).filter('point_id =', int(self.request.get('id'))).get()
        point.title = self.request.get('title')
        point.description = self.request.get('description')
        point.put()
        
        self.redirect('/?pointID='+str(point.point_id))

class DeletePoint(webapp.RequestHandler):
    def post(self):
        map = db.get(self.request.get("key"))
        
        point = Point.all().filter('map_id = ', map.map_id).filter('point_id =', int(self.request.get('id'))).get()
        point.delete()
        
        point = Point.all().filter('map_id = ', map.map_id).order('title').get()
        
        self.redirect('/?pointID='+str(point.point_id))
        
        
class ShowJson(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'

		query = Map.all()
		query.filter('map_id =', int(self.request.get('mapID')))
		query.filter('map_ver =', int(self.request.get('mapVer')))
		map = query.get()

		if map:
			point_result = Point.all().filter('map_id =', int(self.request.get('mapID'))).fetch(1000)
			points = []
			for res in point_result:
				points.append({"pointID": res.point_id,
					           "title": res.title,
							   "description": res.description,
							   "coord": {"x": res.x, "y": res.y},
							   "photo": []})

			result = {"mapID": map.map_id,
				 	  "mapVer": map.map_ver,
				      "title": map.title,
				      "map": "http://indoorposition.appspot.com/map_image?key=%s" % map.key(),
					  "points": points}
			self.response.out.write(simplejson.dumps(result))
		else:
			self.error(404)

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/upload_map', UploadMap),
                                      ('/map_image', MapImage),
                                      ('/drop_map', DropMap),
                                      ('/update_map', UpdateMap),
                                      ('/qr_all', QRAll),
                                      ('/add_point', AddPoint),
									  ('/show', ShowJson),
                                      ('/update_point', UpdatePoint),
                                      ('/delete_point', DeletePoint)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
