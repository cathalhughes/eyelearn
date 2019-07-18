from __future__ import print_function
import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import MaxPooling2D, Convolution2D
from scipy.io import loadmat
from keras.utils import np_utils
import numpy as np
import pickle

from os import path
import os

from scipy.io import loadmat
from scipy.misc import imsave
import numpy as np
import pickle


## This part is borrowed from https://github.com/Coopss/EMNIST
def load_data(mat_file_path, width=28, height=28, max_=None, verbose=True):
    ''' Load data in from .mat file as specified by the paper.
        Arguments:
            mat_file_path: path to the .mat, should be in sample/
        Optional Arguments:
            width: specified width
            height: specified height
            max_: the max number of samples to load
            verbose: enable verbose printing
        Returns:
            A tuple of training and test data, and the mapping for class code to ascii value,
            in the following format:
                - ((training_images, training_labels), (testing_images, testing_labels), mapping)
    '''
    # Local functions
    def rotate(img):
        # Used to rotate images (for some reason they are transposed on read-in)
        flipped = np.fliplr(img)
        return np.rot90(flipped)

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

    # Load convoluted list structure form loadmat
    mat = loadmat(mat_file_path)

    # Load char mapping
    mapping = {kv[0]:kv[1:][0] for kv in mat['dataset'][0][0][2]}
    pickle.dump(mapping, open('mapping1.p', 'wb' ))

    # Load training data
    if max_ == None:
        max_ = len(mat['dataset'][0][0][0][0][0][0])
    training_images = mat['dataset'][0][0][0][0][0][0][:max_].reshape(max_, height, width, 1)
    training_labels = mat['dataset'][0][0][0][0][0][1][:max_]

    # Load testing data
    if max_ == None:
        max_ = len(mat['dataset'][0][0][1][0][0][0])
    else:
        max_ = int(max_ / 6)
    testing_images = mat['dataset'][0][0][1][0][0][0][:max_].reshape(max_, height, width, 1)
    testing_labels = mat['dataset'][0][0][1][0][0][1][:max_]

    # Reshape training data to be valid
    if verbose == True: _len = len(training_images)
    for i in range(len(training_images)):
        if verbose == True: print('%d/%d (%.2lf%%)' % (i + 1, _len, ((i + 1)/_len) * 100), end='\r')
        training_images[i] = rotate(training_images[i])
    if verbose == True: print('')

    # Reshape testing data to be valid
    if verbose == True: _len = len(testing_images)
    for i in range(len(testing_images)):
        if verbose == True: print('%d/%d (%.2lf%%)' % (i + 1, _len, ((i + 1)/_len) * 100), end='\r')
        testing_images[i] = rotate(testing_images[i])
    if verbose == True: print('')

    # Convert type to float32
    training_images = training_images.astype('float32')
    testing_images = testing_images.astype('float32')

    # Normalize to prevent issues with model
    training_images /= 255
    testing_images /= 255

    training_labels = training_labels - 1
    testing_labels = testing_labels - 1
    nb_classes = len(mapping)

    return ((training_images, training_labels), (testing_images, testing_labels), mapping, nb_classes)
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

    y_train = np_utils.to_categorical(y_train[np.newaxis], num_classes)
    y_test = np_utils.to_categorical(y_test[np.newaxis], num_classes)

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
    mat_path = 'emnist-letters.mat'
    height = 28
    width = 28
    max = None
    verbose = True

    ((training_images, training_labels), (testing_images, testing_labels), mapping, num_classes) = load_data(mat_path, width, height, max, verbose)
    print(num_classes)
    #print(type())
    list = training_labels.T[0].tolist()
    print(np_utils.to_categorical(list, 26))
    model = build_cnn(num_classes, input_shape=(28,28,1))

    train_model(model, training_images, training_labels, testing_images, testing_labels, batch_size, epochs, num_classes)

if __name__ == '__main__':
    main()