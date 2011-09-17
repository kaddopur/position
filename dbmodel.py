from google.appengine.ext import db

class Map(db.Model):
    author = db.UserProperty(required=True)
    map_id = db.IntegerProperty(required=True)
    map_ver = db.IntegerProperty()
    title = db.StringProperty()
    file = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    
class Point(db.Model):
    map_id = db.IntegerProperty(required=True)
    point_id = db.IntegerProperty(required=True)
    title = db.StringProperty()
    description = db.StringProperty()
    x = db.IntegerProperty()
    y = db.IntegerProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    
class PointPhoto(db.Model):
    map_id = db.IntegerProperty()
    point_id = db.IntegerProperty()
    file = db.BlobProperty()
    date = db.DateTimeProperty(auto_now_add=True)
