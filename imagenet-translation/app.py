from flask import Flask, request, Response, render_template, flash, redirect, url_for
from keras.applications.inception_v3 import preprocess_input
from keras.preprocessing.image import load_img, img_to_array
from keras.applications.inception_v3 import decode_predictions
import numpy as np
from model.load_model import *
from PIL import Image, ExifTags
from get_translation_google import *
from flask import jsonify


app = Flask(__name__)
app.secret_key = "MY_SECRET_KEY"
VALID_EXTENSIONS = ["png", "jpg", "jpeg"]

model, graph = loadInception()

@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template("index.html")


@app.route('/translateObject', methods=['POST'])
def translateObject():
    print(request.headers)
    print(request.files['image1'])
    image = request.files['image1']
    image.save("object.png")
    language = request.form['language']
    print(language)
    basewidth = 300
    try:
        image = Image.open("object.png")
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())

        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)
        wpercent = (basewidth / float(image.size[0]))
        hsize = int((float(image.size[1]) * float(wpercent)))
        image = image.resize((basewidth, hsize), Image.ANTIALIAS)
        image.save("object.png")
        image.close()

    except (AttributeError, KeyError, IndexError):
        # cases: image don't have getexif
        pass

    target_size = (299,299)
    image = processImage("object.png", target_size)
    with graph.as_default():
        results = model.predict(image)
        labels = decode_predictions(results)
        print(labels)
        translations = get_translation(labels[0], language)
        print(translations)
        print(labels)


    response = []
    for i in range(len(labels[0])):
        translation = translations[i]
        english = labels[0][i][1]
        english = english.split("_")
        english = " ".join(english)
        print(english)
        confidence = round(labels[0][i][2] * 100, 2)
        response.append((translation, english, confidence))

    json = {'predictions': response}
    print(json)
    return jsonify(json)
    #return render_template("index.html", results=response)

#@app.route('/classroom', methods=['GET', 'POST'])



def processImage(filename, target_size):
    img = load_img(filename, target_size=target_size)
    x = img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    return x

#app.run("localhost", port=5001)
