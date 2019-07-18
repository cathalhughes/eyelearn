import keras
import numpy as np
from keras.applications import vgg16, inception_v3, resnet50, mobilenet, xception, vgg19
from app import processImage
import os
import cv2 as cv


target_size = (224,224)

# Load the VGG model
vgg_model = vgg16.VGG16(weights='imagenet', input_shape=(224,224,3))

vgg19_model = vgg19.VGG19(weights='imagenet', input_shape=(224,224,3))

# Load the Inception_V3 model
inception_model = inception_v3.InceptionV3(weights='imagenet', input_shape=(224,224,3))

# Load the ResNet50 model
resnet_model = resnet50.ResNet50(weights='imagenet', input_shape=(224,224,3))

# Load the MobileNet model
mobilenet_model = mobilenet.MobileNet(weights='imagenet', input_shape=(224,224,3))

xception_model = xception.Xception(weights='imagenet', input_shape=(224,224,3))

font = cv.FONT_HERSHEY_SIMPLEX
for image in os.listdir(".\\images"):
    if os.path.isdir(os.path.join(".\\images", image)):
        print("--------")
        continue
    imgStr = ""

    predictions = []
    path = os.path.join(".\\images", image)
    newPath = os.path.join(".\\images\\predictions\\", "pred_" + image)
    image = processImage(path, target_size)
    vgg = vgg16.decode_predictions(vgg_model.predict(image))
    print(vgg)
    vggStr = "VGG16: " + vgg[0][0][1] + " " + str(vgg[0][0][2] * 100)[:5] + "%"
    inc = inception_v3.decode_predictions(inception_model.predict(image))
    vgg_19 = vgg19.decode_predictions(vgg19_model.predict(image))
    vgg19Str = "VGG19: " + vgg_19[0][0][1] + " " + str(vgg_19[0][0][2] * 100)[:5] + "%"
    incStr = "Inception V3: " +  inc[0][0][1] + " " + str(inc[0][0][2] * 100)[:5] + "%"
    res = resnet50.decode_predictions(resnet_model.predict(image))
    resStr = "ResNet 50: " + res[0][0][1] + " " + str(res[0][0][2] * 100)[:5] + "%"
    mob = mobilenet.decode_predictions(mobilenet_model.predict(image))
    mobStr = "MobileNet: " + mob[0][0][1] + " " + str(mob[0][0][2] * 100)[:5] + "%"
    xce = xception.decode_predictions(xception_model.predict(image))
    xceStr = "Xception: " + xce[0][0][1] + " " + str(xce[0][0][2] * 100)[:5] + "%"

    imgStr =  vggStr + "\n" + vgg19Str + "\n" + incStr + "\n" + resStr + "\n" + mobStr + "\n" + xceStr + "\n"
    print(imgStr)
    img = cv.imread(path)
    y0, dy = 50, 30
    for i, line in enumerate(imgStr.split('\n')):
        y = y0 + i * dy
        cv.putText(img, line, (50, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, 2, 2)
    cv.imwrite(newPath, img)