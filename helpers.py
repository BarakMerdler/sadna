import cv2
import pyzbar.pyzbar as pyzbar
import numpy as np
import pytesseract
from twilio.rest import Client
from decouple import config


def decode(img):
    img = './images/rfidCde.png'
    image = cv2.imread(img)
    decodedObjects = pyzbar.decode(image)
    for obj in decodedObjects:
        return obj.data.decode("utf-8")
    return None

    # img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # try:
    #    data = pytesseract.image_to_string(img_rgb)
    #    print("success")
    #    print(data)
    #    return (data)
    # except Exception as e:
    #    print(e)
    #    return None


def twilioHandle(phone):
    # Your Account SID from twilio.com/console
    account_sid = config('ACCOUNT_SID')
    # Your Auth Token from twilio.com/console
    auth_token = config('AUTH_TOKEN')

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        to=config(phone),
        from_=config('FROM_NUM'),
        body="Your pet is ready to come back home :)")

    return(message.sid)
