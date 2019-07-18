from numpy import array
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM, CuDNNLSTM
from keras.preprocessing.sequence import TimeseriesGenerator
from matplotlib import pyplot
# define dataset
series = array([60, 65, 55, 60, 70, 75, 72, 67, 73, 76, 70, 59, 63, 54, 66, 70, 80, 71, 63, 65, 79, 84, 80, 81, 82, 75, 69, 60, 70, 77, 79, 84])

train_size = int(len(series) * 0.8)
train, test = series[0:train_size], series[train_size:len(series)]
print('Observations: %d' % (len(series)))
print('Training Observations: %d' % (len(train)))
print('Testing Observations: %d' % (len(test)))

pyplot.plot(train)
pyplot.plot([None for i in train] + [x for x in test])
#pyplot.show()

# reshape to [10, 1]
n_features = 1
train = train.reshape((len(train), 1))
# define generator
n_input = 3
generator = TimeseriesGenerator(train, train, length=n_input, batch_size=8)
# define model
model = Sequential()
model.add(LSTM(100, activation='relu', input_shape=(n_input, n_features)))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')
# fit model
model.fit_generator(generator, steps_per_epoch=1, epochs=500, verbose=0)
# make a one step prediction out of sample

x_input = array([77, 79, 84]).reshape((1, n_input, n_features))

test = test.reshape((len(test), 1))
# define generator
n_input = 3
generator = TimeseriesGenerator(test, test, length=n_input, batch_size=8)

print(model.evaluate_generator(generator))


yhat = model.predict(x_input, verbose=0)
print(yhat)