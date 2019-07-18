from __future__ import print_function
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import MaxPooling2D, Convolution2D
from scipy.io import loadmat
from keras.utils import np_utils
import numpy as np
import pickle

def load_data(mat_path, width, height, max, verbose):
    mat = loadmat(mat_path)
    mapping = {kv[0]: kv[1:][0] for kv in mat['dataset'][0][0][2]}
    pickle.dump(mapping, open('mapping.p', 'wb'))

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

    if max == None:
        max = len(mat['dataset'][0][0][0][0][0][0])
    training_images = mat['dataset'][0][0][0][0][0][0][:max].reshape(max, height, width, 1)
    training_labels = mat['dataset'][0][0][0][0][0][1][:max]

    if max == None:
        max = len(mat['dataset'][0][0][1][0][0][0])
    else:
        max = int(max / 6)
    testing_images = mat['dataset'][0][0][1][0][0][0][:max].reshape(max, height, width, 1)
    testing_labels = mat['dataset'][0][0][1][0][0][1][:max]

    if verbose == True: _len = len(training_images)
    for i in range(len(training_images)):
        if verbose == True: print('%d/%d (%.2lf%%)' % (i + 1, _len, ((i + 1) / _len) * 100), end='\r')
        training_images[i] = rotate_image(training_images[i])
    if verbose == True: print('')

    if verbose == True: _len = len(testing_images)
    for i in range(len(testing_images)):
        if verbose == True: print('%d/%d (%.2lf%%)' % (i + 1, _len, ((i + 1) / _len) * 100), end='\r')
        testing_images[i] = rotate_image(testing_images[i])
    if verbose == True: print('')

    img = display(training_images[7])
    print(img)

    training_images = training_images.astype('float32')
    testing_images = testing_images.astype('float32')

    training_images /= 255
    testing_images /= 255

    num_classes = len(mapping)

    return ((training_images, training_labels), (testing_images, testing_labels), mapping, num_classes)

def rotate_image(image):
    rotated_image = np.fliplr(image)

    return np.rot90(rotated_image)

def build_cnn(num_classes, input_shape):
    model = Sequential()
    model.add(Convolution2D(32, kernel_size=(3, 3),
                     activation='relu',
                     padding='valid',
                     input_shape=input_shape))
    model.add(Convolution2D(32, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    model.add(Flatten())
    model.add(Dense(512, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation='softmax'))

    return model

def train_model(model, x_train, y_train, x_test, y_test, batch_size, epochs, num_classes):
    early_stopping = keras.callbacks.EarlyStopping(monitor='val_loss',
                                                   min_delta=0,
                                                   patience=4,
                                                   verbose=1, mode='auto')

    model.compile(loss='categorical_crossentropy',
                  optimizer='adadelta',
                  metrics=['accuracy'])

    y_train = np_utils.to_categorical(y_train, num_classes)
    y_test = np_utils.to_categorical(y_test, num_classes)

    model.fit(x_train, y_train,
              batch_size=batch_size,
              epochs=epochs,
              verbose=1,
              validation_data=(x_test, y_test))

    score = model.evaluate(x_test, y_test, verbose=0)
    print('Test loss:', score[0])
    print('Test accuracy:', score[1])

    model.save("EMNIST_Handwritten_Letters.h5")


def main():

    batch_size = 256
    epochs = 20
    mat_path = 'emnist-byclass2.mat'
    height = 28
    width = 28
    max = None
    verbose = True

    ((training_images, training_labels), (testing_images, testing_labels), mapping, num_classes) = load_data(mat_path, width, height, max, verbose)
    print(num_classes)
    model = build_cnn(num_classes, input_shape=(28,28,1))

    #train_model(model, training_images, training_labels, testing_images, testing_labels, batch_size, epochs, num_classes)

if __name__ == '__main__':
    main()