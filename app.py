from flask import Flask, render_template, request, Response, redirect, url_for, session
import time
from helpers import decode
from flask_debugtoolbar import DebugToolbarExtension
import os
from passlib.hash import sha256_crypt
from datetime import datetime
from pymongo import MongoClient
from bson import json_util, ObjectId, BSON
import json


app = Flask(__name__)


app.jinja_env.filters['zip'] = zip

# !--- For debugging switch to true ---!
app.debug = True

# for session
app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
# toolbar = DebugToolbarExtension(app)

#! Set the DB connection
client = MongoClient(
    'mongodb+srv://sadna:sadna1234@cluster0-duigw.mongodb.net/test?retryWrites=true&w=majority')
db = client['petcare']
#! Set the tables
users = db['users']
vet = db['veterinarys']
customers = db['customers']
activePet = db['activePet']
pets = db['pets']
medicalhistory = db['medicalhistory']

#! DB functions get/set


def findCustomer(email):
    return customers.find_one({"email": email})


def findUser(email):
    return users.find_one({"email": email})


def findVet(vetId):
    return vet.find_one({"_id": vetId})


def findPet(petId):
    return pets.find_one({"_id": petId})


def findActivePet(vedId):
    return activePet.find({"vet_id": vedId})


def removeFromActive(petId):
    return activePet.delete_one({"pet_id": petId})


def updatePetPlace(petId, newPlace):
    result = activePet.update_one(
        {"pet_id": int(petId)}, {"$set": {"place": str(newPlace)}})
    return result.modified_count


def getMedicalHistory(petId):
    return medicalhistory.find({"pet_id": petId})


PATH_TO_TEST_IMAGES_DIR = './images'

#! Class of pet


class animal(object):
    def __init__(self, _id, _name, _type):
        self._id = _id
        self._name = _name
        self._type = _type


class activeAnimal(object):
    def __init__(self, animal, place):
        self.animal = animal
        self.place = place


# Route for login as a user
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
            vetId = user['veterinary_id']
            vet = findVet(vetId)
            vetId_sanitized = json.loads(json_util.dumps(vetId))
            session['vetId'] = vetId_sanitized
            session['vet_name'] = vet['name']
            session['no_oper_room'] = vet['no_oper_room']
            session['no_cage'] = vet['no_cage']
            return redirect(url_for('home'))
        return render_template('/landingPage.html', error='Please check your email and/or password')
    return render_template('/landingPage.html')

# Route of the main app
@app.route('/home', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return 'POST at HOME'
    activePetInVet = findActivePet(session['vetId'])
    petCage = []
    petOper = []
    petTemp = []
    petWaiting = []
    for pet in activePetInVet:
        tempPet = findPet(pet['pet_id'])
        tempAnimal = animal(pet['pet_id'], tempPet['name'], tempPet['type'])
        setAnimal = activeAnimal(tempAnimal, pet['place'])
        if pet['place'] == 'oper':
            petOper.append(setAnimal)
        if pet['place'] == 'cage':
            petCage.append(setAnimal)
        if pet['place'] == 'temp':
            petTemp.append(setAnimal)
        if pet['place'] == 'waiting':
            petWaiting.append(setAnimal)
    return render_template('/home.html', petCage=petCage, petOper=petOper, petTemp=petTemp, petWaiting=petWaiting)

# Route to add pet (new or no)
@app.route('/addpet', methods=['GET', 'POST'])
def addpet():
    if request.method == 'POST':
        userDetails = request.form
        email = userDetails['email']
        if (findCustomer(email)):
            return redirect(url_for('setNewPetTreatment', email=email))
        return redirect(url_for('addNewCustomer', email=email))
    return render_template('/customers.html')

# Route to set new customer and his pets
@app.route('/addNewCustomer', methods=['GET', 'POST'])
def addNewCustomer():
    customerMail = request.args['email']
    if request.method == 'POST':
        petsNames = request.form.getlist('name')
        petsTypes = request.form.getlist('type')
        userName = request.form['custNmae']
        petsId = []
        for i in range(len(petsNames)):
            petid = pets.count_documents({}) + 1
            newPet = {
                "_id": petid,
                "name": petsNames[i],
                "type": petsTypes[i],
                "active": False,
                "medicalHistoryId": [],
                "date_created": datetime.utcnow()
            }
            try:
                pets.insert_one(newPet)
            except Exception as e:
                print(e)
            try:
                petsId.append(petid)
            except Exception as e:
                print(e)
        newCust = {
            "email": customerMail,
            "name": userName,
            "pet_id": petsId,
            "date_created": datetime.utcnow()
        }
        try:
            customers.insert_one(newCust)
        except Exception as e:
            print(e)

        return redirect(url_for('setNewPetTreatment', email=customerMail))
    return render_template('/setNewPet.html', customerMail=customerMail)


# Route to set the pet to treatment
@app.route('/setNewPetTreatment', methods=['GET', 'POST'])
def setNewPetTreatment():
    if request.method == 'POST':
        petId = int(request.form['petsId'])
        medicalId = medicalhistory.count_documents({}) + 1
        try:
            pets.update_one({"_id": petId}, {
                "$set": {
                    "active": True
                }
            })
        except Exception as e:
            print(e)
        try:
            newActivePet = {
                "pet_id": petId,
                "vet_id": session['vetId'],
                "place": "waiting",
                "currentMedicalId": medicalId,
                "startDate": datetime.utcnow()
            }
            activePet.insert_one(newActivePet)
        except Exception as e:
            print(e)
        try:
            newMedical = {
                "_id": medicalId,
                "vet_id": session['vetId'],
                "pet_id": petId,
                "startDate": datetime.utcnow()
            }
            medicalhistory.insert_one(newMedical)
        except Exception as e:
            print(e)
        try:
            pets.update_one({"_id": petId}, {
                "$push": {
                    "medicalHistoryId": medicalId
                }
            })
        except Exception as e:
            print(e)
        return redirect(url_for('home'))
    customerMail = request.args['email']
    customer = findCustomer(customerMail)
    cusromerPets = []
    for pet_id in customer['pet_id']:
        pet = findPet(pet_id)
        cusromerPets.append(animal(pet['_id'], pet['name'], pet['type']))
    return render_template('/setNewPetTreatment.html', cusromerPets=cusromerPets, customerMail=customerMail, addNewPet=1)

# Route to updtae the facilty in the vet
@app.route('/vetAdmin', methods=['GET', 'POST'])
def vetAdmin():
    return render_template('/editingRooms.html')

# Route to set new user in a new vent
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        userDetails = request.form
        userName = userDetails['fullName']
        userMail = userDetails['email']
        if findUser(userMail):
            return render_template('/adminLogIn.html', error='Mail is alredy in use')
        userPassword = sha256_crypt.encrypt(userDetails['password'])
        newUser = {
            "email": userMail,
            "name": userName,
            "password": userPassword,
            "admin": True,
            "date_created": datetime.utcnow()
        }
        try:
            users.insert_one(newUser)
            return redirect(url_for('vetInit', email=userMail))
        except Exception as e:
            print(e)
    return render_template('/adminLogIn.html')

# Route to add another user for vet
@app.route('/AdminAddUser', methods=['GET', 'POST'])
def AdminAddUser():
    if request.method == 'POST':
        data = request.get_json()
        userName = data['name']
        userMail = data['email']
        admin = bool(data['admin'])
        userPassword = sha256_crypt.encrypt(data['password'])
        if findUser(userMail):
            return json.dumps({'success': False, 'error': e}), 500, {'ContentType': 'application/json'}
        newUser = {
            "email": userMail,
            "name": userName,
            "password": userPassword,
            "admin": admin,
            "date_created": datetime.utcnow(),
            "veterinary_id": session['vetId']
        }
        try:
            users.insert_one(newUser)
            return redirect(url_for('home'))
        except Exception as e:
            print(e)
            return json.dumps({'success': False, 'error': e}), 500, {'ContentType': 'application/json'}
    return render_template('/adminLogIn.html', oldUser=1)

# Route to set new vent
@app.route('/admin/vet', methods=['GET', 'POST'])
def vetInit():
    userMail = request.args['email']
    if request.method == 'POST':
        vetDetails = request.form
        vetName = vetDetails['name']
        vetAddress = vetDetails['address']
        vetId = vet.count_documents({}) + 1
        newVet = {
            "_id": vetId,
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

    return render_template('/vetInit.html')


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

# API to remove pet from active care
@app.route('/removePetFromClink')
def removePetFromClink():
    activePetInVet = findActivePet(session['vetId'])
    animals = []
    for pet in activePetInVet:
        tempPet = findPet(pet['pet_id'])
        tempAnimal = animal(pet['pet_id'], tempPet['name'], tempPet['type'])
        animals.append(tempAnimal)
    return render_template('/removePetFromClink.html', animals=animals)


@app.route('/deleteFromActive', methods=['POST'])
def deleteFromActive():
    data = request.get_json()
    petId = int(data['id'])
    discharge_note = data['dischargeNote']
    print(discharge_note)
    print(petId)
    try:
        petMedicalId = activePet.find_one({"pet_id": petId})
        medicalId = int(petMedicalId['currentMedicalId'])
        medicalhistory.update_one({"_id": medicalId}, {
            '$set': {
                "endDate": datetime.utcnow(),
                'discharge_note': discharge_note
            }
        })
        removeFromActive(petId)
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    except Exception as e:
        print(e)
        return Response("{'error':'%s'}" % (e), status=404, mimetype='application/json')

# Set new pet to customer exsits
@app.route('/updatePetToCust', methods=['POST'])
def updatePetToCust():
    data = request.get_json()
    newName = data['newName']
    newType = data['newType']
    customer = data['customer']
    petid = pets.count_documents({}) + 1
    newPet = {
        "_id": petid,
        "name": newName,
        "type": newType,
        "active": False,
        "medicalHistoryId": [],
        "date_created": datetime.utcnow()
    }
    try:
        pets.insert_one(newPet)
    except Exception as e:
        print(e)
        return json.dumps({'success': False, 'error': e}), 500, {'ContentType': 'application/json'}
    try:
        customers.update_one({"email": customer}, {
            "$push": {"pet_id": petid}
        })
    except Exception as e:
        print(e)
        return json.dumps({'success': False, 'error': e}), 500, {'ContentType': 'application/json'}
    return json.dumps({'success': True, 'newName': newName, 'newType': newType, 'customer': customer, 'petId': petid}), 200, {'ContentType': 'application/json'}

# API to update facilty
@app.route('/updateFacilty', methods=['POST'])
def updateFacilty():
    data = request.get_json()
    by = int(data['by'])
    place = data['place']
    vetId = session['vetId']
    try:
        vet.update_one({"_id": vetId}, {
            "$inc": {place: by}
        })
        session[place] += by
    except Exception as e:
        return json.dumps({'success': False, 'error': e}), 500, {'ContentType': 'application/json'}
    return json.dumps({'success': True, 'place': place, 'by': by}), 200, {'ContentType': 'application/json'}

# API to update place for pet at the vet
@app.route('/update')
def update():
    animals = []
    activePetInVet = findActivePet(session['vetId'])
    for pet in activePetInVet:
        tempPet = findPet(pet['pet_id'])
        tempAnimal = animal(pet['pet_id'], tempPet['name'], tempPet['type'])
        animals.append(activeAnimal(tempAnimal, pet['place']))
    return render_template('/update.html', animals=animals)


@app.route('/updateActivePetPlace', methods=['POST'])
def updateActivePetPlace():
    data = request.get_json()
    petId = data['id']
    newPlace = data['place']
    try:
        x = updatePetPlace(petId, newPlace)
    except Exception as e:
        print(e)
        return Response("{'error':'%s'}" % (e), status=404, mimetype='application/json')
    return 'success'


@app.route('/api', methods=['GET', 'POST'])
def api():
    return render_template('/api.html')


@app.route('/addTreatmentToPet', methods=['POST'])
def addTreatmentToPet():
    data = request.get_json()
    petId = data['id']
    newTreatment = data['newTreatment']
    newDrug = data['newDrug']
    activePets = activePet.find_one({"pet_id": petId})
    medicalId = activePets['currentMedicalId']
    try:
        medicalhistory.update_one({"_id": medicalId}, {
            "$push": {
                "treatments": newTreatment,
                "drugs": newDrug,
                "time": datetime.utcnow()
            }
        })
    except Exception as e:
        print(e)
        return Response("{'error':'%s'}" % (e), status=404, mimetype='application/json')
    return 'success'


@app.route('/treatmentLog', methods=['POST', 'GET'])
def treatmentLog():
    med = []
    PeitId = request.args.get('id')
    med_history = getMedicalHistory(int(PeitId))
    for medical in med_history:
        med.append(medical)
    return render_template('/treatmentLog.html', med=med)


@app.route('/searchpettotreatment', methods=['GET', 'POST'])
def searchpettotreatment():
    if request.method == 'POST':
        userDetails = request.form
        email = userDetails['email']
        if (findCustomer(email)):
            return redirect(url_for('searcsetNewPetTreatment', email=email))
        return render_template('/customers.html', error=1)
    return render_template('/customers.html')


@app.route('/searcsetNewPetTreatment', methods=['GET', 'POST'])
def searcsetNewPetTreatment():
    if request.method == 'POST':
        petId = int(request.form['petsId'])
        return redirect(url_for('treatmentLog', id=petId))
    customerMail = request.args['email']
    customer = findCustomer(customerMail)
    cusromerPets = []
    for pet_id in customer['pet_id']:
        pet = findPet(pet_id)
        cusromerPets.append(animal(pet['_id'], pet['name'], pet['type']))
    return render_template('/setNewPetTreatment.html', cusromerPets=cusromerPets)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop("name", None)
    session.pop("admin", None)
    session.pop("vetId", None)
    session.pop("vet_name", None)
    session.pop("no_oper_room", None)
    session.pop("no_cage", None)
    return redirect(url_for('index'))


@app.context_processor
def utility_processor():
    def get_pic(animal):
        return{
            'cow': "cow.png",
            'giraffe': "giraffe.png",
            'lion': "lion.jpg",
            'pinguin': "pinguin.jpg",
            'tiger': "tiger.png"
        }.get(animal, 'tiger.png')
    return dict(get_pic=get_pic)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=80)
