from __future__ import print_function
import keras
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K
from mnist import MNIST
from sklearn.model_selection import train_test_split
from keras.callbacks import ModelCheckpoint

batch_size = 128
num_classes = 26
epochs = 50


img_rows, img_cols = 28, 28

input_shape = (img_rows, img_cols, 1)

def load_data():
    emnist_data = MNIST(path="data", return_type='numpy')
    emnist_data.select_emnist('letters')
    X, y = emnist_data.load_training()

    X = X.reshape(124800, 28, 28)
    y = y.reshape(124800, 1)

    y = y-1

    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=111)

    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)

    def display(img, threshold=0.5):
        # Debugging only
        render = ''
        for row in img:
            for col in row:
                if col > threshold:
                    render += '@'
                else:
                    render += '.'
            render += '\n'
        return render

    img = display(x_train[5])
    print(img)
    print(y_train[5])

    x_train = x_train.astype('float32')
    x_test = x_test.astype('float32')

    x_train /= 255
    x_test /= 255

    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)

    return x_train, y_train, x_test, y_test


def build_cnn():
    model = Sequential()
    model.add(Conv2D(32, kernel_size=(3, 3),
                            activation='relu',
                            padding='valid',
                            input_shape=input_shape))
    model.add(Conv2D(32, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    model.add(Flatten())
    model.add(Dense(512, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation='softmax'))


    model.compile(loss=keras.losses.categorical_crossentropy,
                  optimizer=keras.optimizers.Adadelta(),
                  metrics=['accuracy'])

    return model

def train_model(model, x_train, y_train, x_test, y_test):

    checkpoint = ModelCheckpoint('EMNIST_Handwritten_Letters_V2_checkpoint2.h5', monitor='val_loss', verbose=1, save_best_only=True, mode='min')

    model.fit(x_train, y_train,
              batch_size=batch_size,
              epochs=epochs,
              verbose=1,
              validation_data=(x_test, y_test),
              callbacks=[checkpoint])

    score = model.evaluate(x_test, y_test, verbose=0)
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])


x_train, y_train, x_test, y_test = load_data()

model = build_cnn()

#train_model(model, x_train, y_train, x_test, y_test)




