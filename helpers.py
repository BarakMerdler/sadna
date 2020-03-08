import cv2
import pyzbar.pyzbar as pyzbar
import numpy as np


def decode(img):
    image = cv2.imread(img)
    decodedObjects = pyzbar.decode(image)
    for obj in decodedObjects:
        return obj.data
    return None
