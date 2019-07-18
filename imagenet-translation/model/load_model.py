from keras.applications.inception_v3 import InceptionV3
import tensorflow as tf

def loadInception():
    print("Inception Model Loading")
    model = InceptionV3(input_shape=(299,299,3), include_top=True, weights='imagenet', classes=1000)
    print("Inception Model Loaded")
    graph = tf.get_default_graph()
    return model, graph