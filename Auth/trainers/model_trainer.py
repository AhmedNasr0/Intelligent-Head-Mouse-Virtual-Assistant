import os
import tensorflow as tf
from datetime import datetime
import matplotlib.pyplot as plt
from tensorflow.keras.metrics import Precision, Recall
import numpy as np
from tqdm import tqdm
import time
from models.final_model import L1Dist
from models.base_model import CustomWeightInitializer, CustomBiasInitializer
import pandas as pd
from data_utils.data_preprocessing import preprocess

# Enable GPU memory growth
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("GPU is available and configured")
    except RuntimeError as e:
        print(f"GPU configuration error: {e}")
else:
    print("No GPU found. Using CPU")

class ModelTrainer:
    def __init__(self, model, epochs=100, learning_rate=0.00006):
        self.model = model
        self.epochs = epochs
        self.learning_rate = learning_rate
        self.optimizer = None
        self.loss = None

    def train(self, train_data, val_data):
        self.model.compile(optimizer=self.get_optimizer(), loss=self.get_loss(), metrics=["accuracy"])
        
        # Unpack the data into anchor and validation images
        train_data = train_data.map(lambda x, y, z: ((x, y), z))
        val_data = val_data.map(lambda x, y, z: ((x, y), z))
        
        history = self.model.fit(train_data, epochs=self.epochs, validation_data=val_data)
        self.save_model(history,self.optimizer,self.loss)
        return history
    
    def evaluate(self, test_data):
        return self.model.evaluate(test_data)

    def visualize_history(self, history):
        plt.figure(figsize=(10, 5))
        plt.plot(history.history['accuracy'], label='Training Accuracy')
        plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.legend()
        

        plt.figure(figsize=(10, 5))
        plt.plot(history.history['loss'], label='Training Loss')
        plt.plot(history.history['val_loss'], label='Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.show()
        
    
    def save_model(self, history, optimizerName, lossRate):
        if not os.path.exists("saved_models"):
            os.makedirs("saved_models")
            
        # Get string representations of optimizer and loss
        optimizer_str = "adam" if isinstance(self.optimizer, tf.keras.optimizers.Adam) else "sgd"
        loss_str = "binary_ct" if isinstance(self.loss, tf.keras.losses.BinaryCrossentropy) else "mean_squared_error"
        
        filename = f"saved_models/model_acc{history.history['accuracy'][-1]:.2f}_{optimizer_str}_{loss_str}_{datetime.now().strftime('%Y%m%d')}.keras"
        self.model.save(filename)
    
    def set_loss(self, loss):
        if loss == 'binary_CT':
            self.loss = tf.keras.losses.BinaryCrossentropy()
        else:
            raise ValueError(f"Invalid loss: {loss}")
    
    def get_loss(self):
        return self.loss
    
    def get_optimizer(self):
        return self.optimizer
    
    def set_optimizer(self, optimizer):
        if optimizer == 'adam':
            self.optimizer = tf.keras.optimizers.Adam(learning_rate=self.learning_rate)
        elif optimizer == 'sgd':
            self.optimizer = tf.keras.optimizers.SGD(learning_rate=self.learning_rate, momentum=0.6, nesterov=True, decay=0.0003)
        else:
            raise ValueError(f"Invalid optimizer: {optimizer}")
        
    def test_model(self, test_data, model_path):
        # Define custom objects
        custom_objects = {
            'CustomWeightInitializer': CustomWeightInitializer,
            'CustomBiasInitializer': CustomBiasInitializer,
            'L1Dist': L1Dist
        }
        
        # Load model with custom objects
        self.model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
        
        # Preprocess test data to match training data format
        test_data = test_data.map(lambda x, y, z: ((x, y), z))
        
        # Compile model with same settings as training
        self.model.compile(optimizer=self.get_optimizer(), loss=self.get_loss(), metrics=["accuracy"])
        
        # Evaluate model and create history-like object
        return self.model.evaluate(test_data)
        
    def predict(self, input_image_path, validation_image_path, model_path):
        # Define custom objects
        custom_objects = {
            'CustomWeightInitializer': CustomWeightInitializer,
            'CustomBiasInitializer': CustomBiasInitializer,
            'L1Dist': L1Dist
        }

        # Load model with custom objects
        self.model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
        
        input_image = preprocess(input_image_path)
        validation_image = preprocess(validation_image_path)
        # تأكد أن الصور بنفس الأبعاد ومتوافقة مع النموذج
        input_image = tf.expand_dims(input_image, axis=0)  # إضافة بُعد للدفعة
        validation_image = tf.expand_dims(validation_image, axis=0)

        # توقع التشابه بين الصورتين
        prediction = self.model.predict([input_image, validation_image])

        return prediction

        
