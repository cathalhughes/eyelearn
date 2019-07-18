import os
import glob
import numpy as np
from tensorflow.keras import layers
from tensorflow import keras
import tensorflow as tf
from random import randint
import matplotlib.pyplot as plt


def load_data(root, vfold_ratio=0.2, max_items_per_class=4000):
    all_files = glob.glob(os.path.join(root, '*.npy'))

    # initialize variables
    x = np.empty([0, 784])
    y = np.empty([0])
    class_names = []

    # load each data file
    for idx, file in enumerate(all_files):
        data = np.load(file)
        data = data[0: max_items_per_class, :]
        labels = np.full(data.shape[0], idx)

        x = np.concatenate((x, data), axis=0)
        y = np.append(y, labels)

        class_name, ext = os.path.splitext(os.path.basename(file))
        class_names.append(class_name)

    data = None
    labels = None

    # randomize dataset
    permutation = np.random.permutation(y.shape[0])
    x = x[permutation, :]
    y = y[permutation]

    # training and testing
    vfold_size = int(x.shape[0] / 100 * (vfold_ratio * 100))

    x_test = x[0:vfold_size, :]
    y_test = y[0:vfold_size]

    x_train = x[vfold_size:x.shape[0], :]
    y_train = y[vfold_size:y.shape[0]]
    return x_train, y_train, x_test, y_test, class_names

def preprocess_data():
    x_train, y_train, x_test, y_test, class_names = load_data('data')
    num_classes = len(class_names)
    image_size = 28

    # Reshape and normalize
    x_train = x_train.reshape(x_train.shape[0], image_size, image_size, 1).astype('float32')
    x_test = x_test.reshape(x_test.shape[0], image_size, image_size, 1).astype('float32')

    x_train /= 255.0
    x_test /= 255.0

    # Convert class vectors to class matrices
    y_train = keras.utils.to_categorical(y_train, num_classes)
    y_test = keras.utils.to_categorical(y_test, num_classes)

    return x_train, y_train, x_test, y_test, class_names

def create_model(x_train):
    model = keras.Sequential()
    model.add(layers.Convolution2D(16, (3, 3),
                                   padding='same',
                                   input_shape=x_train.shape[1:], activation='relu'))
    model.add(layers.MaxPooling2D(pool_size=(2, 2)))
    model.add(layers.Convolution2D(32, (3, 3), padding='same', activation='relu'))
    model.add(layers.MaxPooling2D(pool_size=(2, 2)))
    model.add(layers.Convolution2D(64, (3, 3), padding='same', activation='relu'))
    model.add(layers.MaxPooling2D(pool_size=(2, 2)))
    model.add(layers.Flatten())
    model.add(layers.Dense(128, activation='relu'))
    model.add(layers.Dense(100, activation='softmax'))

    adam = tf.train.AdamOptimizer()
    model.compile(loss='categorical_crossentropy',
                  optimizer=adam,
                  metrics=['top_k_categorical_accuracy'])

    return model

def train_model(model, x_train, y_train, x_test, y_test):
    model.fit(x=x_train, y=y_train, validation_split=0.1, batch_size=256, verbose=2, epochs=5)
    score = model.evaluate(x_test, y_test, verbose=0)
    print('Test accuracy: {:0.2f}%'.format(score[1] * 100))
    return model

def test_inference(model, x_test, class_names):
    idx = randint(0, len(x_test))
    img = x_test[idx]
    plt.imshow(img.squeeze())
    prediction = model.predict(np.expand_dims(img, axis=0))[0]
    ind = (-prediction).argsort()[:5]
    latex = [class_names[x] for x in ind]
    print(latex)

def store_classes(class_names):
    with open('class_names.txt', 'w') as file_handler:
        for item in class_names:
            file_handler.write("{}\n".format(item))


x_train, y_train, x_test, y_test, class_names = preprocess_data()
model = create_model(x_train)
model = train_model(model, x_train, y_train, x_test, y_test)
test_inference(model, x_test, class_names)
store_classes(class_names)
model.save('doodle.h5')
