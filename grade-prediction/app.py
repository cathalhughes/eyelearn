from flask import Flask, request, Response, render_template, flash, redirect, url_for
from numpy import array
from keras.preprocessing.sequence import TimeseriesGenerator
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM, CuDNNLSTM
from keras import backend as K

from flask import jsonify


app = Flask(__name__)
app.secret_key = "MY_SECRET_KEY"



@app.route('/getAveragePrediction', methods=['POST'])
def getAveragePrediction():
    data = request.get_json()
    dataArray = data["dataArray"]
    predictions = []
    for data in dataArray:
        if len(data) < 10:
            data = [60, 65, 55, 60, 70, 75, 72, 67, 73, 76, 70, 59, 63, 54, 66, 70, 80, 71, 63, 65, 79, 84, 80, 81, 82, 75, 69, 60, 70, 77, 79, 84]
        generator = getDataGeneratorForData(data)
        model = createModel()
        acc = backTest(model, data) ## if accuaracy low, no prediction.
        trained_model = trainModel(model, generator)
        prediction = getPrediction(trained_model, data[-3:])
        predictions.append(prediction)
        K.clear_session()

    print(predictions)
    return jsonify({"predictions": predictions})

def getDataGeneratorForData(dataArray):
    series = array(dataArray)
    # reshape
    series = series.reshape((len(series), 1))
    # define generator
    generator = TimeseriesGenerator(series, series, length=3, batch_size=8)
    return generator

def createModel():
    model = Sequential()
    model.add(LSTM(100, activation='relu', input_shape=(3, 1)))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mse')
    return model

def trainModel(model, generator):
    model.fit_generator(generator, steps_per_epoch=1, epochs=500, verbose=0)
    return model

def getPrediction(model, data):
    x_input = array(data).reshape((1, 3, 1))
    yhat = model.predict(x_input, verbose=0)
    return int(round(yhat[0][0]))


def backTest(model, data):
    data = array(data)
    train_size = int(len(data) * 0.8)
    train, test = data[0:train_size], data[train_size:len(data)]
    n_features = 1
    train = train.reshape((len(train), 1))

    n_input = 3
    generator = TimeseriesGenerator(train, train, length=n_input, batch_size=8)
    model.fit_generator(generator, steps_per_epoch=1, epochs=500, verbose=0)
    test = test.reshape((len(test), 1))

    n_input = 3
    generator = TimeseriesGenerator(test, test, length=n_input, batch_size=8)

    acc = model.evaluate_generator(generator)
    return acc



#app.run("localhost", port=5006)
