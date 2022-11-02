import json
import os
from tabnanny import check
import psycopg2
import postgres
from dotenv import load_dotenv
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
import time


load_dotenv()  # loads variables from .env file into environment

app = Flask(__name__)

cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)

cors = CORS(app)
url = os.environ.get("DATABASE_URL")  # gets variables from environment

def check_token(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided'},400
        try:
            user = auth.verify_id_token(request.headers.get('Authorization'))
        except:
            return {'message':'Invalid token provided.'},400
        return f(*args, **kwargs)
    return wrap

@app.route("/")
@check_token
def root():
    return {"message": "Welcome to AMA-Nda Backend Service, you are authorized for access", "routes": [{"user":"/api/users"},{"registration":"/api/users/register"},{"req_history":"/api/requests"},{"notifications":"/api/notification"}]}

@app.route("/api/users/register", methods=['POST'])
def user_registers():
    connection = psycopg2.connect(url)
    email = request.json.get('email')
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(postgres.FIND_USER, (email,))
            useremail = cursor.fetchone()
            if useremail is not None:
                if useremail[0] == email:
                    cursor.close()
                    return {"message": f"User {useremail} already exists"}, 403
            cursor.execute(postgres.CREATE_USER, (email,))
            userid = cursor.fetchone()[0]
            cursor.close()
    return {"message": f"User {email} has been created with ID: {userid}"}, 201

@app.route("/api/users", methods=['GET','POST', 'PUT'])
@check_token
def user_signin():
    connection = psycopg2.connect(url)
    if request.method == 'POST':
        email = request.json.get('email')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.FIND_USER, (email,))
                useremail = cursor.fetchone()
                if useremail is not None:
                    if useremail[0] == email:
                        cursor.execute(postgres.UPDATE_SIGNIN, (email,))
                        logintime = cursor.fetchone()[0]
                        cursor.close()
        return {"message": f"User {useremail[0]} session began at {logintime}"}, 201
    
    if request.method == 'GET':
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.SELECT_USERS)
                print('cursor: ', cursor.description)
                columns = [x[0] for x in cursor.description]
                print('columns: ', columns)
                userdata = cursor.fetchall()
                json_data = []
                for result in userdata:
                    json_data.append(dict(zip(columns,result)))
                cursor.close()
        return jsonify(json_data),200

@app.route("/api/requests", methods=['GET', 'POST'])
@check_token
def requests():
    connection = psycopg2.connect(url)
    if request.method == 'GET':
        uid = request.json.get('uid')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.FIND_USER_UID, (uid,))
                request_data = cursor.fetchall()
                if request_data != []:
                    columns = [x[0] for x in cursor.description]
                    json_data = []
                    for result in request_data:
                        json_data.append(dict(zip(columns,result)))
                    cursor.close()
                    return jsonify(json_data),200
            cursor.close()
        return {"message": "No request history found"},200

    if request.method == 'POST':
        uid = request.json.get('uid')
        user_request = request.json.get('user_request')
        ai_response = request.json.get('ai_response')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.INSERT_REQUEST, (uid, user_request, ai_response,))
                request_id = cursor.fetchone()[0]
        return {"message": f"Request #{request_id} Successful"},201

                

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

    # Edit profile route with PUT
    # if request.method == 'PUT':

# @app.route("/api/requests", methods=['GET','POST'])
# def 
