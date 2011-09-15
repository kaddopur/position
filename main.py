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

class Map(db.Model):
    author = db.UserProperty()
    map_id = db.IntegerProperty()
    map_ver = db.IntegerProperty()
    title = db.Text()
    file = db.Blob()
    date = db.DateTimeProperty(auto_now_add=True)
    
class Point(db.Model):
    map_id = db.IntegerProperty()
    point_id = db.IntegerProperty()
    title = db.Text()
    description = db.Text()
    x = db.IntegerProperty()
    y = db.IntegerProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    
class PointPhoto(db.Model):
    map_id = db.IntegerProperty()
    point_id = db.IntegerProperty()
    file = db.Blob()
    date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        
        # after log in
        logout_url = users.create_logout_url(self.request.uri)
        
        query = Map.all()
        query.filter('author =', user)
        query.order('-date')
        map = query.fetch(1)
        
        
        
        template_values = {
            'logout_url': logout_url
        }
            
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))
        

application = webapp.WSGIApplication([('/', MainPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
