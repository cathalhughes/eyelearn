from numpy import array
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM, CuDNNLSTM
from keras.preprocessing.sequence import TimeseriesGenerator
# define dataset
series = array([60, 65, 55, 60, 70, 75, 72, 67, 73, 76, 70, 59, 63, 54, 66, 70, 80, 71, 63, 65, 79, 84, 80, 81, 82, 75, 69, 60, 70, 77, 79, 84])
# reshape to [10, 1]
n_features = 1
series = series.reshape((len(series), n_features))
# define generator
n_input = 3
generator = TimeseriesGenerator(series, series, length=n_input, batch_size=8)
for i in range(len(generator)):
    x, y = generator[i]
    print('%s => %s' % (x, y))
# define model
model = Sequential()
model.add(LSTM(100, activation='relu', input_shape=(n_input, n_features)))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')
# fit model
model.fit_generator(generator, steps_per_epoch=1, epochs=500, verbose=0)
print(model.evaluate_generator(generator))

# make a one step prediction out of sample
x_input = array([77, 79, 84]).reshape((1, n_input, n_features))
yhat = model.predict(x_input, verbose=0)
print(yhat)