from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

@app.route("/health")
def health():
    return {"status": "OK"}, 200

@app.route("/count")
def count():
    count = db.songs.count_documents({})
    return {"count": count}, 200

@app.route("/song", methods=["GET"])
def songs():
    songs = db.songs.find({})
    all_songs = parse_json(songs)
    return {"songs": all_songs}, 200

@app.route("/song", methods=["POST"])
def create_song():
    song_data = request.get_json()
    song_exists = db.songs.find_one({"id": song_data["id"]})
    if song_exists:
        return {"Message": f'song with id {song_data["id"]} already present'}, 302
    db.songs.insert_one(song_data)
    return {"song inserted": song_data["id"]}, 201

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    song = db.songs.find_one({"id": id})
    data = parse_json(song)
    if not data:
        return {"message": f'song of id {id} not found'}, 404
    return {"song": data}, 200

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    song_data = request.get_json()
    song_exists = db.songs.find_one({"id": id})
    if song_exists:
        db.songs.update_one({"id": id}, {"$set": song_data})
        return song_data, 201
    return {"message": "song not found"}, 404

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    c = db.songs.delete_one({"id": id})
    if c.deleted_count == 0:
        return {"message": "song not found"}, 404
    return {}, 204