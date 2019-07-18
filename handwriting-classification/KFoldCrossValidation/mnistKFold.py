from __future__ import print_function
import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K
from sklearn.model_selection import train_test_split
from keras.callbacks import History
from keras import backend as K
import matplotlib.pyplot as plt
import json
import numpy as np

batch_size = 128
num_classes = 10
epochs = 12

# input image dimensions
img_rows, img_cols = 28, 28


def load_data():
# the data, split between train and test sets
	(x_train, y_train), (x_test, y_test) = mnist.load_data()

	if K.image_data_format() == 'channels_first':
	    x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
	    x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
	    input_shape = (1, img_rows, img_cols)
	else:
	    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
	    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
	    input_shape = (img_rows, img_cols, 1)

	x_train = x_train.astype('float32')
	x_test = x_test.astype('float32')
	x_train /= 255
	x_test /= 255
	print('x_train shape:', x_train.shape)
	print(x_train.shape[0], 'train samples')
	print(x_test.shape[0], 'test samples')

	# convert class vectors to binary class matrices
	y_train = keras.utils.to_categorical(y_train, num_classes)
	y_test = keras.utils.to_categorical(y_test, num_classes)

	return x_train, x_test, y_train, y_test, input_shape

def create_model(input_shape):
	model = Sequential()
	model.add(Conv2D(32, kernel_size=(3, 3),
	                 activation='relu',
	                 input_shape=input_shape))
	model.add(Conv2D(64, (3, 3), activation='relu'))
	model.add(MaxPooling2D(pool_size=(2, 2)))
	model.add(Dropout(0.25))
	model.add(Flatten())
	model.add(Dense(128, activation='relu'))
	model.add(Dropout(0.5))
	model.add(Dense(10, activation='softmax'))

	model.compile(loss=keras.losses.categorical_crossentropy,
	              optimizer=keras.optimizers.Adadelta(),
	              metrics=['accuracy'])

	return model

def train_model(model, x_train, y_train, x_test, y_test, i, files, name):
	hist = History()
	early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss',
												   min_delta=0,
												   patience=4,
												   verbose=1, mode='auto')
	model.fit(x_train, y_train,
	          batch_size=batch_size,
	          epochs=epochs,
	          verbose=1,
	          validation_data=(x_test, y_test),
			  callbacks=[early_stopping, hist])


	plt.style.use("ggplot")
	plt.figure()
	N = len(hist.history["val_acc"])
	plt.plot(np.arange(0, N), hist.history["loss"], label="train_loss")
	plt.plot(np.arange(0, N), hist.history["val_loss"], label="val_loss")
	plt.plot(np.arange(0, N), hist.history["acc"], label="train_acc")
	plt.plot(np.arange(0, N), hist.history["val_acc"], label="val_acc")
	plt.title("Training Loss and Accuracy on MNIST")
	plt.xlabel("Epoch #")
	plt.ylabel("Loss/Accuracy")
	plt.legend(loc="lower left")
	plt.savefig("mnistresults" + str(i + 1) + ".png")

	score = model.evaluate(x_test, y_test, verbose=0)
	model.save(name)
	with open(files, "w") as f:
		f.write(json.dumps(hist.history))
		f.write("\nEpochs: " + str(len(hist.history["val_acc"])))
	print(hist.history)
	print('Test loss:', score[0])
	print('Test accuracy:', score[1])

if __name__ == "__main__":
	n_folds = 10
	data, val, labels, val_labels, input_shape = load_data()
	#print(data)
	# skf = StratifiedKFold(n_splits=5)
	# print(skf.get_n_splits(data, labels))
	txtfile = ["kfoldMNIST1one.txt", "kfoldMNIST1two.txt", "kfoldMNIST1three.txt", "kfoldMNIST1four.txt","kfoldMNIST1five.txt"]
	models = ["mnist1.h5","mnist2.h5","mnist5.h5","mnist4.h5"]

	for i in range(0,4):
		print ("Running Fold", i+1, "/", n_folds)
		x_train, x_test, y_train, y_test = train_test_split(data, labels)

		model = None # Clearing the NN.
		model = create_model(input_shape)
		train_model(model, x_train, y_train, x_test, y_test, i, txtfile[i], models[i])
		K.clear_session()