import cv2
import pyzbar.pyzbar as pyzbar
import numpy as np
import pytesseract


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
