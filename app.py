import os
import psycopg2
import postgres
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps


load_dotenv()  # loads variables from .env file into environment

app = Flask(__name__)

cred = credentials.Certificate('fbAdminConfig.json')
firebase = firebase_admin.initialize_app(cred)

cors = CORS(app)
url = os.environ.get("DATABASE_URL")  # gets variables from environment
connection = psycopg2.connect(url)

# @app.before_request
# def before_request():
#     authKey = request.json['authKey']
#     if (authKey != auth):
#         return {"message": "Unauthorized access, invalid authentication details."}, 401

def check_token(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if not request.headers.get('Authorization'):
            return {'message': 'No token provided'},400
        try:
            print(request)
            user = auth.verify_id_token(request.headers.get('Authorization'))
            print('user: ',user)
            uid = user['uid']
        except:
            print(request.headers.get('Authorization'))
            return {'message':'Invalid token provided.'},400
        return f(*args, **kwargs)
    return wrap

@app.route("/api/users/register", methods=['POST'])
def user_registers():
    email = request.form['email']
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(postgres.FIND_USER, (email,))
            useremail = cursor.fetchone()
            if useremail is not None:
                if useremail[0] == email:
                    return {"message": f"User {useremail} already exists"}, 403
            cursor.execute(postgres.CREATE_USER, (email,))
            userid = cursor.fetchone()[0]
            cursor.close()
    return {"message": f"User {email} has been created with ID: {userid}"}, 201

@app.route("/api/users", methods=['GET','POST', 'PUT'])
@check_token
def user_signin():
    if request.method == 'POST':
        email = request.form['email']
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.UPDATE_SIGNIN, (email,))
                logintime = cursor.fetchone()[0]
                cursor.close()
        return {"message": f"User session began at {logintime}"}, 201
    
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
        return jsonify(json_data)

    # Edit profile route with PUT
    # if request.method == 'PUT':

# @app.route("/api/requests", methods=['GET','POST'])
# def 
