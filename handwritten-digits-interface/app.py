from flask import Flask, render_template, request,jsonify
from models.loadModels import *
from controllers.handwrittenInputProcessing import *
import pickle
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, send_wildcard=True)

global emnistModel, emnistGraph


emnistModel, emnistGraph = initEMNISTModel()
mnistModel, mnistGraph = initMNISTModel()

mapping = pickle.load(open('mapping.p', 'rb'))

letters = { 1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e', 6: 'f', 7: 'g', 8: 'h', 9: 'i', 10: 'j',
11: 'k', 12: 'l', 13: 'm', 14: 'n', 15: 'o', 16: 'p', 17: 'q', 18: 'r', 19: 's', 20: 't',
21: 'u', 22: 'v', 23: 'w', 24: 'x', 25: 'y', 26: 'z', 27: '-'}

@app.route('/draw', methods=['GET','POST'])
def handwrittenImagesPage():
    return render_template("draw.html")

@app.route('/predictCharacter', methods=['GET', 'POST'])
def predictCharacter():
    print("here")
    imgPost = request.get_data(as_text=True)
    print(type(imgPost))
    convertHandwrittenImage(imgPost)
    img = processImage('output.png')
    #img /= 255
    with emnistGraph.as_default():
        characterPrediction = emnistModel.predict(img)
        print(characterPrediction)
        response = {'prediction': str(letters[int(np.argmax(characterPrediction) + 1)]),
                    'confidence': str(max(characterPrediction[0]) * 100)[:6]}
        response = jsonify(response)
        print(response)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@app.route('/predictNumber', methods=['GET', 'POST'])
def predictNumber():
    print("here")
    imgPost = request.get_data(as_text=True)
    #print(imgPost)
    convertHandwrittenImage(imgPost)
    img = processImage('output.png')
    #img /= 255
    with mnistGraph.as_default():
        characterPrediction = mnistModel.predict(img)
        print(characterPrediction)
        response = {"prediction": str((np.argmax(characterPrediction[0]))),  #MNIST
                    "confidence": str(max(characterPrediction[0]) * 100)[:6]}
        print(re)
        response = jsonify(response)
        #print(response)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response


#app.run(host='0.0.0.0', port=5002, threaded=True)