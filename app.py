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


load_dotenv() 

app = Flask(__name__)

cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)

cors = CORS(app)
url = os.environ.get("DATABASE_URL")
connection = psycopg2.connect(url)

## This is a wrapper function that checks the request for a valid JWT token. It performs the checks on routes that it's been declared in
def check_token(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided'},400
        try:
            user = auth.verify_id_token(request.headers.get('Authorization'))
        except:
            return {'message':'Invalid token provided.'},401
        return f(*args, **kwargs)
    return wrap

## Root to check yout access via POSTMAN
@app.route("/")
@check_token
def root():
    return {"message": "Welcome to AMA-Nda Backend Service, you are authorized for access", "routes": [{"user":"/api/users"},{"registration":"/api/users/register"},{"req_history":"/api/requests"},{"notifications":"/api/notification"}]}, 200

## User Registration route. Checks for exisiting user email in the DB before creating one
@app.route("/api/users/register", methods=['POST'])
def user_registers():
    email = request.json.get('email')
    uid = request.json.get('uid')
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(postgres.FIND_USER, (email,))
            useremail = cursor.fetchone()
            if useremail is not None:
                if useremail[0] == email:
                    cursor.close()
                    return {"message": f"User {useremail} already exists"}, 403
            cursor.execute(postgres.CREATE_USER, (uid,email,))
            user_data = cursor.fetchall()
            cursor.close()
    return {"message": f"User {user_data[0][1]} has been created with ID: {user_data[0][0]}"}, 201

## User Sign-In route
@app.route("/api/users", methods=['GET','POST', 'PUT'])
@check_token ## Authentication wrapper here
def user_signin():

    ## Updates login count & time. If user not found, will create as successful authentication means user exists in Firebase Auth
    if request.method == 'POST':
        uid = request.json.get('uid')
        email = request.json.get('email')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.FIND_USER, (uid,))
                user_id = cursor.fetchone()
                if user_id is not None:
                    if user_id[0] == uid:
                        cursor.execute(postgres.UPDATE_SIGNIN, (uid,))
                        logintime = cursor.fetchone()[0]
                        cursor.close()
                        return {"message": f"User {user_id[0]} session began at {logintime}"}, 201
                cursor.execute(postgres.CREATE_USER, (uid,email,))
                user_data = cursor.fetchall()
                cursor.close()
        return {"message": f"User {user_data[0][1]} has been created with ID: {user_data[0][0]}"}, 201
    
    ## Retrieves all user data from the DB (no sensitive data such as password)
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
        return json.dumps(json_data, indent=4, default=str)

## Requests route
@app.route("/api/requests", methods=['GET', 'POST'])
@check_token ## Authentication wrapper here
def requests():

    ## Retrieves all successful requests & details made by the user to the openAI API
    if request.method == 'GET':
        uid = request.args.get('uid', type = str)
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.FIND_USER_REQUESTS, (uid,))
                request_data = cursor.fetchall()
                if request_data != []:
                    json_data = []
                    columns = [x[0] for x in cursor.description]
                    for result in request_data:
                        json_data.append(dict(zip(columns,result)))
                    cursor.close()
                    return json.dumps(json_data, indent=4, default=str)
            cursor.close()
        return {"message": "No request history found"},204

    ## Inserts details of successful requests made by the user to the openAI API
    if request.method == 'POST':
        uid = request.json.get('uid')
        user_request = request.json.get('user_request')
        ai_response = request.json.get('ai_response')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.INSERT_REQUEST, (uid, user_request, ai_response,))
                request_id = cursor.fetchone()[0]
        return {"message": f"Request #{request_id} Successful"},201

## Notifications route
@app.route("/api/notifications", methods=['GET','POST', 'PUT', 'DELETE'])
@check_token ## Authentication wrapper here
def notifications():

    ## Retrieves all notifications sent to the user by Administrators
    if request.method == 'GET':
        uid = request.args.get('uid', type = str)
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.FIND_USER_NOTIFICATIONS, (uid,))
                request_data = cursor.fetchall()
                if request_data != []:
                    columns = [x[0] for x in cursor.description]
                    json_data = []
                    for result in request_data:
                        json_data.append(dict(zip(columns,result)))
                    cursor.close()
                    return json.dumps(json_data, indent=4, default=str),200
            cursor.close()
        return {"message": "You have no notifications!"},204

    ## Route only authorized for access by Administrators to send notifications to users
    if request.method == 'POST':
        admin_uid = request.json.get('admin_uid')
        users_uid = request.json.get('users_uid')
        message = request.json.get('message')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.CHECK_ADMIN, (admin_uid,))
                admin = cursor.fetchone()
                if admin is not None:
                    if len(users_uid) == 1:
                        cursor.execute(postgres.SEND_NOTIFICATIONS, (admin[0], message, users_uid[0]))
                        cursor.close()
                        return {"message": f"Successfully sent User ID: {users_uid[0]} the notification"},201
                    for user in users_uid:
                        cursor.execute(postgres.SEND_NOTIFICATIONS, (admin[0], message, user))
                    cursor.close()
                    notf_num = len(users_uid)
                    return {"message": f"Successfully sent {notf_num} notification(s)"},201
        return {"message": "You do not have adminstrative privileges to perform this task."},403

    ## This allows users to set notification visibility for their archiving
    if request.method == 'PUT':
        nid = request.json.get('nid')
        visible = request.json.get('visible')
        with connection:
            with connection.cursor() as cursor:
                print(request.json)
                cursor.execute(postgres.UPDATE_NOTE_VIS, (visible, nid))
                cursor.close()
        return {"message": "Notification cleared!"},201

    ## This allows users to delete notifications. Currently not in use within the app due to technical issues
    if request.method == 'DELETE':
        nid = request.json.get('nid')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.DELETE_NOTE, (nid,))
                cursor.close()
        return {"message": "Notification deleted!"},200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
