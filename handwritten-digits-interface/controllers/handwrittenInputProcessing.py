import re
import numpy as np
from scipy.misc import imread, imresize
import base64

def convertHandwrittenImage(imgData):
    imgStr = re.search(r'base64,(.*)',imgData)
    if imgStr != None:
        imgStr = imgStr.group(1)
    else:
        imgStr = imgData

    #print(imgStr)
    with open('output.png','wb') as output:
        output.write(base64.b64decode(imgStr))

def processImage(filename):
    img = imread(filename, mode='L')
    img = np.invert(img)
    img = imresize(img, (28,28))
    img = img.astype('float32') ##processImage helps emnis5t ##miuch f amuchness with mnits
    img = img.reshape(1,28,28,1)
    img /= 255 ##helps emnist much of a muchness with mnistr

    return img