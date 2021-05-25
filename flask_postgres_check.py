from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:koij890hgf@localhost/postgres"
app.config['JSON_AS_ASCII'] = False
app.debug = True
db = SQLAlchemy(app)

class Photos(db.Model):
    __tablename__='photos'
    photo_id = db.Column(db.Integer(), primary_key=True)
    photo_description = db.Column(db.String(200), nullable=True)
    photo_uri = db.Column(db.String(500), nullable=False)
    likes = db.Column(db.Integer(), nullable=False, default=0)
    
    def __init__(self, photo_description, photo_uri):
        self.photo_description = photo_description
        self.photo_uri = photo_uri

@app.route('/test', methods=['GET'])
def test():
    return {
        'test':'test1'
    }

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/get_photos', methods=['GET'])
def getFotos():
    allPhotos = Photos.query.all()
    output = []
    for photo in allPhotos:
        currentPhoto = {}
        currentPhoto['photo_description'] = photo.photo_description
        currentPhoto['photo_uri'] = photo.photo_uri
        currentPhoto['likes'] = photo.likes
        output.append(currentPhoto)
    return jsonify(output)

app.run()