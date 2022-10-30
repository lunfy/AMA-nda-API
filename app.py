import os
import psycopg2
import postgres
from dotenv import load_dotenv
from flask import Flask, request, json

load_dotenv()  # loads variables from .env file into environment

app = Flask(__name__)
url = os.environ.get("DATABASE_URL")  # gets variables from environment
auth = os.environ.get("FIREBASE_AUTH")
connection = psycopg2.connect(url)

@app.before_request
def before_request():
    authKey = request.form['authKey']
    if (authKey != auth):
        return {"message": "Unauthorized access, invalid authentication details."}, 401

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
    return {"message": f"User {email} has been created with ID: {userid}"}, 201

@app.route("/api/users", methods=['POST', 'PUT'])
def user_signin():
    if request.method == 'POST':
        email = request.form['email']
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(postgres.UPDATE_SIGNIN, (email,))
                logintime = cursor.fetchone()[0]
                print('1: ', {cursor})
                cursor.close()
                print('2: ', cursor)
        return {"message": f"User session began at {logintime}"}, 201
    
    # Edit profile route with PUT
    # if request.method == 'PUT':