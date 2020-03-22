from flask import Flask, render_template, request, Response, redirect, url_for, session
import time
from helpers import decode
from flask_debugtoolbar import DebugToolbarExtension
import os
from passlib.hash import sha256_crypt
from datetime import datetime
from pymongo import MongoClient

app = Flask(__name__)

# !--- For debugging switch to true ---!
app.debug = True


app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
toolbar = DebugToolbarExtension(app)

#! Set the DB connection
client = MongoClient(
    'mongodb+srv://sadna:sadna1234@cluster0-duigw.mongodb.net/test?retryWrites=true&w=majority')
db = client['petcare']
#! Set the tables
users = db['users']
vet = db['veterinarys']

#! DB functions get/set


def findUser(email):
    return users.find_one({"email": email})


def findVet(vetId):
    return vet.find_one({"_id": vetId})


PATH_TO_TEST_IMAGES_DIR = './images'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        userDetails = request.form
        userEmail = userDetails['email']
        user = findUser(userEmail)
        userPass = userDetails['password']
        if user and sha256_crypt.verify(userPass, user["password"]):
            session['name'] = user['name']
            session['admin'] = user['admin']
            vet = findVet(user['veterinary_id'])
            session['vet_name'] = vet['name']
            session['no_oper_room'] = vet['no_oper_room']
            session['no_cage'] = vet['no_cage']
            #!------------------------------!
            # TODO get the active care animals
            #!------------------------------!
            return render_template('/veterinary.html')
        return render_template('/home.html', error='Please check your email and password')
    return render_template('/home.html')


@app.route('/vetAdmin', methods=['GET', 'POST'])
def vetAdmin():
    return 'success'


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        userDetails = request.form
        userName = userDetails['fullName']
        userMail = userDetails['email']
        if findUser(userMail):
            return render_template('/adminLogIn.html', numPage=1, error='Mail is alredy in use')
        userPassword = sha256_crypt.encrypt(userDetails['password'])
        newUser = {
            "email": userMail,
            "name": userName,
            "password": userPassword,
            "admin": True,
            "super_admin": True,
            "date_created": datetime.utcnow()
        }
        try:
            users.insert_one(newUser)
            return redirect(url_for('vetInit', email=userMail))
        except Exception as e:
            print(e)
    return render_template('/adminLogIn.html', numPage=1)


@app.route('/admin/vet', methods=['GET', 'POST'])
def vetInit():
    userMail = request.args['email']
    if request.method == 'POST':
        vetDetails = request.form
        vetName = vetDetails['name']
        vetAddress = vetDetails['address']
        newVet = {
            "name": vetName,
            "address": vetAddress,
            "no_oper_room": 0,
            "no_cage": 0,
            "date_created": datetime.utcnow()
        }
        try:
            vetId = vet.insert_one(newVet).inserted_id
        except Exception as e:
            print(e)
        try:
            users.update_one({"email": userMail}, {
                             "$set": {"veterinary_id": vetId}})
            return redirect(url_for('index'))
        except Exception as e:
            print(e)

    return render_template('/vetInit.html', numPage=2)


@app.route('/video')
def video():
    return render_template('/video.html')

# save the image as a picture
@app.route('/image', methods=['POST'])
def image():
    i = request.files['image']  # get the image
    f = ('%s.jpeg' % time.strftime("%Y%m%d-%H%M%S"))
    i.save('%s/%s' % (PATH_TO_TEST_IMAGES_DIR, f))
    data = decode('%s/%s' % (PATH_TO_TEST_IMAGES_DIR, f))
    os.remove('%s/%s' % (PATH_TO_TEST_IMAGES_DIR, f))
    return Response("%s saved./n data: %s " % (f, data))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
