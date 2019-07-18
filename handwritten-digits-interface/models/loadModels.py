from keras.models import load_model
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf


def initEMNISTModel():
    print("EMNIST Model loading....")
    model = load_model('EMNIST_Handwritten_Letters_V2_checkpoint2.h5')
    print("EMNIST Model Loaded")
    graph = tf.get_default_graph()
    return model, graph

def initMNISTModel():
    print("MNIST Model loading....")
    model = load_model("MNIST_Handwritten_Digits.h5")
    print("MNIST Model Loaded")
    graph = tf.get_default_graph()
    return model, graph

