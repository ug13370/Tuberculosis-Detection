# -*- coding: utf-8 -*-
"""lung_segmentation.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17wiFMmFwaQE2WE1kPu891wDDTRaBM-V-
"""

!python --version

!nvidia-smi

# !pip install tensorflow==2.3.1

# !pip install keras==2.3.1

!pip install tensorflow_gpu

import tensorflow as tf
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)

    except RuntimeError as e:
        print(e)

# Commented out IPython magic to ensure Python compatibility.
import numpy as np 
import tensorflow as tf
# config = tf.compat.v1.ConfigProto()
# config.gpu_options.allow_growth = True
# sess = tf.compat.v1.Session(config=config)
import pandas as pd
import os
from cv2 import imread
import cv2
# %matplotlib inline
import matplotlib.pyplot as plt

print(tf.__version__)

from google.colab import drive
drive.mount('/content/drive')

!cp /content/drive/MyDrive/segmentation/segmentation.zip .

!unzip segmentation.zip

!cp /content/drive/MyDrive/7000_images/Dataset.zip .

!unzip Dataset.zip

image_path = "/content/drive/MyDrive/segmentation/cxr"
mask_path = "/content/drive/MyDrive/segmentation/mask"

image_path = "/content/segmentation/cxr"
mask_path = "/content/segmentation/mask"

images = []
masks = []
image_dict = {}
mask_dict = {}
X_shape = 256

for img in os.listdir(image_path):
  im = cv2.cvtColor(cv2.imread(os.path.join(image_path,img)),cv2.COLOR_BGR2GRAY)
  im = cv2.resize(im,(X_shape,X_shape))
  image_dict[img.split(".png")[0]] = im

for mask in os.listdir(mask_path):
  mas = cv2.cvtColor(cv2.imread(os.path.join(mask_path,mask)),cv2.COLOR_BGR2GRAY)
  mas = cv2.resize(mas,(X_shape,X_shape))
  mask_name = mask.split(".png")[0]
  mask_name = mask_name.split("_mask")[0]
  mask_dict[mask_name] = mas

for x in sorted(image_dict):
  images.append(image_dict[x])

for x in sorted(mask_dict):
  masks.append(mask_dict[x])

images = np.array(images).reshape(len(images),256,256,1)
masks = np.array(masks).reshape(len(masks),256,256,1)

masks.shape

plt.imshow(np.squeeze(images[602]))
plt.show()

plt.imshow(np.squeeze(masks[602]))
plt.show()

# from tensorflow import keras
from tensorflow.keras.layers import *
from tensorflow.keras.optimizers import *
from tensorflow.keras.metrics import *
from tensorflow.keras import backend as keras
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import ModelCheckpoint, LearningRateScheduler
from tensorflow.keras.models import *



def dice_coef(y_true, y_pred):
    y_true_f = keras.flatten(y_true)
    y_pred_f = keras.flatten(y_pred)
    intersection = keras.sum(y_true_f * y_pred_f)
    return (2. * intersection + 1) / (keras.sum(y_true_f) + keras.sum(y_pred_f) + 1)

def dice_coef_loss(y_true, y_pred):
    return -dice_coef(y_true, y_pred)

def unet(input_size):
    inputs = Input(input_size)
    
    conv1 = Conv2D(32, (3, 3), activation='relu', padding='same')(inputs)
    conv1 = Conv2D(32, (3, 3), activation='relu', padding='same')(conv1)
    pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

    conv2 = Conv2D(64, (3, 3), activation='relu', padding='same')(pool1)
    conv2 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv2)
    pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)

    conv3 = Conv2D(128, (3, 3), activation='relu', padding='same')(pool2)
    conv3 = Conv2D(128, (3, 3), activation='relu', padding='same')(conv3)
    pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)

    conv4 = Conv2D(256, (3, 3), activation='relu', padding='same')(pool3)
    conv4 = Conv2D(256, (3, 3), activation='relu', padding='same')(conv4)
    pool4 = MaxPooling2D(pool_size=(2, 2))(conv4)

    conv5 = Conv2D(512, (3, 3), activation='relu', padding='same')(pool4)
    conv5 = Conv2D(512, (3, 3), activation='relu', padding='same')(conv5)

    up6 = concatenate([Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same')(conv5), conv4], axis=3)
    conv6 = Conv2D(256, (3, 3), activation='relu', padding='same')(up6)
    conv6 = Conv2D(256, (3, 3), activation='relu', padding='same')(conv6)

    up7 = concatenate([Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(conv6), conv3], axis=3)
    conv7 = Conv2D(128, (3, 3), activation='relu', padding='same')(up7)
    conv7 = Conv2D(128, (3, 3), activation='relu', padding='same')(conv7)

    up8 = concatenate([Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(conv7), conv2], axis=3)
    conv8 = Conv2D(64, (3, 3), activation='relu', padding='same')(up8)
    conv8 = Conv2D(64, (3, 3), activation='relu', padding='same')(conv8)

    up9 = concatenate([Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(conv8), conv1], axis=3)
    conv9 = Conv2D(32, (3, 3), activation='relu', padding='same')(up9)
    conv9 = Conv2D(32, (3, 3), activation='relu', padding='same')(conv9)

    conv10 = Conv2D(1, (1, 1), activation='sigmoid')(conv9)

    return Model(inputs=[inputs], outputs=[conv10])

model = unet(input_size=(512,512,1))
model.summary()

from keras.callbacks import ModelCheckpoint, LearningRateScheduler, EarlyStopping, ReduceLROnPlateau
weight_path="{}_weights.best.hdf5".format('cxr_reg')

checkpoint = ModelCheckpoint(weight_path, monitor='val_loss', verbose=1, 
                             save_best_only=True, mode='min', save_weights_only = True)

reduceLROnPlat = ReduceLROnPlateau(monitor='val_loss', factor=0.5, 
                                   patience=3, 
                                   verbose=1, mode='min', epsilon=0.0001, cooldown=2, min_lr=1e-6)
early = EarlyStopping(monitor="val_loss", 
                      mode="min", 
                      patience=15) 
callbacks_list = [checkpoint, early, reduceLROnPlat]

from tensorflow.keras.optimizers import Adam 
from sklearn.model_selection import train_test_split

model.compile(optimizer=Adam(lr=2e-4,beta_1=0.9), 
              loss=[dice_coef_loss], 
           metrics = [dice_coef, 'binary_accuracy'])

train_images, test_images, train_masks, test_masks = train_test_split((images-127.0)/127.0, 
                                                            (masks>127).astype(np.float32), 
                                                            test_size = 0.1,random_state = 56)

train_images, validation_images, train_masks, validation_masks = train_test_split(train_images,train_masks, 
                                                                 test_size = 0.1, 
                                                                 random_state = 56)

loss_history = model.fit(x = train_images,
                       y = train_masks,
                         batch_size = 16,
                  epochs = 50,
                  validation_data =(validation_images,validation_masks) ,
                  callbacks=callbacks_list)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize = (10, 5))
ax1.plot(loss_history.history['loss'], '-', label = 'Loss')
ax1.plot(loss_history.history['val_loss'], '-', label = 'Validation Loss')
ax1.legend()

ax2.plot(100*np.array(loss_history.history['binary_accuracy']), '-', 
         label = 'Accuracy')
ax2.plot(100*np.array(loss_history.history['val_binary_accuracy']), '-',
         label = 'Validation Accuracy')
ax2.legend()

!cp /content/drive/MyDrive/cxr_reg_weights.best.hdf5 .

model.load_weights('/content/drive/MyDrive/cxr_reg_weights.best.hdf5')

pred_candidates = np.random.randint(1,test_images.shape[0],10)
preds = model.predict(test_images)

plt.figure(figsize=(20,10))

for i in range(0,9,3):
    plt.subplot(3,3,i+1)
    
    plt.imshow(np.squeeze(test_images[pred_candidates[i]]))
    plt.xlabel("Base Image")
    
    
    plt.subplot(3,3,i+2)
    plt.imshow(np.squeeze(test_masks[pred_candidates[i]]))
    plt.xlabel("Mask")
    
    plt.subplot(3,3,i+3)
    plt.imshow(np.squeeze(preds[pred_candidates[i]]))
    plt.xlabel("Pridiction")

imag = cv2.cvtColor(cv2.imread('/content/18.jpg'),cv2.COLOR_BGR2GRAY)
imag = cv2.resize(imag,(256,256))

newimg = []
newimg.append(imag)
newimg = np.array(newimg).reshape(1,256,256,1)
newimg = (newimg - 127.0)/127.0
newimg.shape

predg = model.predict(newimg)

predg = predg.astype(np.int8)

newimg = []
newimg.append(imag)
newimg = np.array(newimg).reshape(1,512,512,1)

image_f = cv2.bitwise_and(newimg,newimg,mask = predg)

#Mask
plt.imshow(np.squeeze(newimg[0]),cmap='gray')
plt.show()


NonTub_path = "/content/Dataset/TB_Chest_Radiography_Database/Normal"
Tub_path = "/content/Dataset/TB_Chest_Radiography_Database/Tuberculosis"


NonTub = []
Tub = []

X_shape = 256

for img in os.listdir(NonTub_path):
  temp = cv2.cvtColor(cv2.imread(os.path.join(NonTub_path,img)),cv2.COLOR_BGR2GRAY)
  temp = cv2.resize(temp,(X_shape,X_shape))
  NonTub.append(temp)
  

for img in os.listdir(Tub_path):
  temp = cv2.cvtColor(cv2.imread(os.path.join(Tub_path,img)),cv2.COLOR_BGR2GRAY)
  temp = cv2.resize(temp,(X_shape,X_shape))
  Tub.append(temp)

NonTub = np.array(NonTub).reshape(len(NonTub),512,512,1)
Tub = np.array(Tub).reshape(len(Tub),512,512,1)

NonTub_norms = (NonTub - 127.0)/127.0
Tub_norms = (Tub - 127.0)/127.0

del NonTub
del Tub

NonTub_preds = model.predict(NonTub_norms)
Tub_preds = model.predict(Tub_norms)

NonTub_preds = NonTub_preds.astype(np.int8)
Tub_preds = Tub_preds.astype(np.int8)

NonTub_segmented = cv2.bitwise_and(NonTub,NonTub,mask = NonTub_preds)
Tub_segmented = cv2.bitwise_and(Tub,Tub,mask = Tub_preds)

plt.imshow(np.squeeze(NonTub_segmented[282]),cmap='gray')
plt.show()

plt.imshow(np.squeeze(NonTub[282]),cmap='gray')
plt.show()

plt.imshow(np.squeeze(Tub_segmented[0]),cmap='gray')
plt.show()

plt.imshow(np.squeeze(Tub_segmented[1]),cmap='gray')
plt.show()

NonTub_segmented=NonTub_segmented.reshape(len(NonTub_segmented),512,512)
Tub_segmented=Tub_segmented.reshape(len(Tub_segmented),512,512)

os.chdir("/content/drive/MyDrive/images/segmented/NonTub")
for i in range(len(NonTub_segmented)):
  cv2.imwrite(str(i)+".jpg",NonTub_segmented[i])

os.chdir("/content/drive/MyDrive/images/segmented/Tub")
for i in range(len(Tub_segmented)):
  cv2.imwrite(str(i)+".jpg",Tub_segmented[i])
