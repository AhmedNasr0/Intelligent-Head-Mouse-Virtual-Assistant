import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, BatchNormalization, Dropout
from tensorflow.keras.models import Model
from .BaseModel import BaseModel

from .utils import CustomWeightInitializer, CustomBiasInitializer


class BaseEmbeddingModel(BaseModel):
    def __init__(self):
        self.base_model = self.build_model()
    
    def build_model(self):
        inp = Input(shape=(105, 105, 3), name='input_image')

        # First block
        c1 = Conv2D(64, (10,10), activation='relu', kernel_initializer=CustomWeightInitializer(), bias_initializer=CustomBiasInitializer())(inp)
        b1 = BatchNormalization()(c1)
        m1 = MaxPooling2D(pool_size=(2,2), padding='same')(b1)
        
        # Second block
        c2 = Conv2D(128, (7,7), activation='relu', kernel_initializer=CustomWeightInitializer(), bias_initializer=CustomBiasInitializer())(m1)
        b2 = BatchNormalization()(c2)
        m2 = MaxPooling2D(pool_size=(2,2), padding='same')(b2)

        # Third block
        c3 = Conv2D(128, (4,4), activation='relu', kernel_initializer=CustomWeightInitializer(), bias_initializer=CustomBiasInitializer())(m2)
        b3 = BatchNormalization()(c3)
        m3 = MaxPooling2D(pool_size=(2,2), padding='same')(b3)

        # Final embedding block
        c4 = Conv2D(256, (4,4), activation='relu', kernel_initializer=CustomWeightInitializer(), bias_initializer=CustomBiasInitializer())(m3)
        b4 = BatchNormalization()(c4)
        f1 = Flatten()(b4)
        d1 = Dense(4096, activation='sigmoid',kernel_regularizer=tf.keras.regularizers.l2(0.01))(f1)

        return Model(inputs=inp, outputs=d1, name='base_model')

    def get_model(self):
        return self.base_model

