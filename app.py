from flask import Flask, render_template, request, Response
import time
from helpers import decode
from flask_debugtoolbar import DebugToolbarExtension
import os

app = Flask(__name__)

# !--- For debugging switch to true ---!
app.debug = True

app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
toolbar = DebugToolbarExtension(app)


PATH_TO_TEST_IMAGES_DIR = './images'


@app.route('/')
def index():
    return render_template('/hello.html')

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
    app.run(host='0.0.0.0')
