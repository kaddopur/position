from google.appengine.ext import db

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