from keras.preprocessing.image import ImageDataGenerator
from PIL import Image
import numpy as np 

location = ""
saveLocation = ""

train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True)

train_generator = train_datagen.flow_from_directory(
    location,
    target_size=(224, 224),
    batch_size=200,
    class_mode='binary',
    save_to_dir=saveLocation,
    save_prefix='N',
    save_format='jpeg')

i = 0
for batch in train_generator:
	# img = Image.fromarray(im, 'RGB')
	# img.save('example/image' + str(i) + '.png')
	i += 1
	if i > 3:
		break


print('Photos Saved!')