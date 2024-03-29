# mongo.py
import json
from validator import validate_user
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
from flask_jwt_extended import (create_access_token,
                                jwt_required, jwt_refresh_token_required, get_jwt_identity,
                                JWTManager)
from flask_bcrypt import Bcrypt
import pymongo
from bson.objectid import ObjectId
import datetime
from bson.json_util import dumps


app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'restdb'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/restdb'
app.config['JWT_SECRET_KEY'] = "wpQhkqNSPuegdBF7x_1FFaqcnuB41FJqfdkW9MNua4w4uvR7ghigyA37tlxkzLOn-ystuZ4CUMJICFXvvTWFyuJ857Dp5pBQsf_RN1iO7V7W5o9zbJFnwPHx8a3hcJqeWPIogjLD_b2nCq5wXt_epNyEaqwMlgCp_tmNApe3lvHPZh6DXVQh0bHWA5f2TrMcApctGiVy3y22mmdF_I-mvxgJcgJbsWvhNZw4Ijl9NtzwdDo"

class JSONEncoder(json.JSONEncoder):
    ''' extend json-encoder class'''

    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, set):
            return list(o)
        if isinstance(o, datetime.datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

mongo = PyMongo(app)

flask_bcrypt = Bcrypt(app)

jwt = JWTManager(app)

mongo.db.users.create_index("email", unique=True)

@app.route('/register', methods=['POST'])
def register():
    ''' register user endpoint '''
    data = validate_user(request.get_json())
    if data['ok']:
        data = data['data']
        data['password'] = flask_bcrypt.generate_password_hash(
                            data['password'])
        try:
          user = mongo.db.users.insert_one(data)
        except pymongo.errors.DuplicateKeyError:
          return jsonify({'status': False, 'message': 'Email already Exist'}), 400
        
        return (jsonify({'status': True, 'message': 'User created successfully!'}), 200)
    else:
        return jsonify({'status': False, 'message': 'Bad request parameters: {}'.format(data['message'])}), 400

@app.route('/login', methods=['POST'])
def login():
    ''' auth endpoint '''
    data = request.get_json()
    user = mongo.db.users.find_one({'email': data['email']})
    if user and \
         flask_bcrypt.check_password_hash(user['password'],
            data['password']):
        del user['password']
        del data['password']
        access_token = create_access_token(identity=data)
        return jsonify({'ok': True, 'data': access_token}), 200
    else:
        return jsonify({'ok': False, 'message': 'invalid username or password'}), 401

@app.route('/results', methods=['POST'])
def results():
    ''' register user endpoint '''
    data = request.get_json()
    user = mongo.db.users.find_one({'email': data['email']})
    if user:
        data_list = []
        for std in range(1, user["standard"]):
            if data["results"][std-1]["standard"] == std:
                data["results"][std-1]["student"] = user["_id"]
                data_list.append(data["results"][std-1]) 
        results = mongo.db.results.insert_many(data_list)
        return jsonify({'ok': True, 'data': results}), 200
    else:
        return jsonify({'ok': False, 'message': 'invalid username or password'}), 401


@app.route('/results', methods=['GET'])
@jwt_required
def previous_results():
    ''' route read user '''
    if request.method == 'GET':
        token_data = get_jwt_identity()
        user = mongo.db.users.find_one({'email': token_data['email']})
        data = mongo.db.results.find({"student": user["_id"]})
        data_list = []
        for result in data:
          data_list.append(result)
        return jsonify({'ok': True, 'data': data_list}), 200

if __name__ == '__main__':
    app.run(debug=True)