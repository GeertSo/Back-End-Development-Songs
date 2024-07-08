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

######################################################################
# INSERT CODE HERE
######################################################################

@app.route("/health")
def health():
    return {'status':'OK'}, 200

@app.route("/count")
def count_songs():
    try:
        cnt = db.songs.count_documents({})
        return {'count': cnt}, 200
    except:
        return {"message": "no valid database"}, 500

@app.route("/song")
def songs():
    try:
        songs = db.songs.find({})
        sl = parse_json(songs)
        return {"songs": sl}, 200
    except:
        return {"message": "no valid database"}, 500

@app.route("/song/<int:id>")
def get_song_by_id(id):
    song_found = db.songs.find({'id':id}, {})
    s = parse_json(song_found)
    if s:
        return {"message": s}
    return {"message": "id not found"}, 404

@app.route("/song", methods=['POST']) 
def create_song():
    new_song = data
    if not new_song:
        return {"message": "song content missing"}, 204
    try:
        # check if new_song.id already exists
        id = new_song['id']
        song_found = db.songs.find({'id':id}, {})
        s = parse_json(song_found)
        if s:
            return {"Message": "song with id "+ str(id) + " already present"}, 302
    except:
        return {"message": "song content missing"}, 204

    res = db.songs.insert_one(new_song)

    new_oid = parse_json(db.songs.find({'id':id}, {}))[0]['_id']
    return {"inserted id": new_oid}, 201

    # alternative way to get the oid, but with a different format
    #return {"inserted id": f"{res.inserted_id}"}, 201

@app.route("/song/<int:id>", methods=['PUT']) 
def update_song(id):
    updated_song = request.json
    
    if not updated_song:
        return {"message": "update content missing"}, 204
    try:
        result = db.songs.update_one({'id':id}, {'$set': updated_song})

        existing = result.raw_result['updatedExisting']
        modified = result.raw_result['nModified']
        if existing:
            if modified > 0:
                song = parse_json(db.songs.find({'id':id}, {}))[0]
                return {"updated song": song}, 201
            else:
                return {"message": "song found, but nothing updated"}, 200
        return {"message": "song not found"}, 404
    except:
        return {"message": "somthing going wrong"}, 500

@app.route("/song/<int:id>", methods=['DELETE'])
def delete_song(id):
    try:
        result = db.songs.delete_one({'id':id})
        if result.acknowledged:
            del_cnt = result.deleted_count
            if del_cnt == 0:
                return {"message": "song not found"}, 404
            return {}, 204
        return {"message": "somthing going wrong"}, 500
    except:
        return {"message": "somthing going wrong"}, 500

