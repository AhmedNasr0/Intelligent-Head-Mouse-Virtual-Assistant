import tensorflow as tf
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.models import Model
from .BaseModel import BaseModel

from .base_model import BaseEmbeddingModel
from .distance_layers import L1Dist

class FinalModel(BaseModel):
    def __init__(self):
        self.base_model = BaseEmbeddingModel().get_model()
        self.model = self.build_model()

    def build_model(self):
        # Input layers
        input_image = Input(name='input_img', shape=(105,105,3))
        validation_image = Input(name='validation_img', shape=(105,105,3))

        input_embedding = self.base_model(input_image)
        validation_embedding = self.base_model(validation_image)

        distance_layer = L1Dist()
        distances = distance_layer(input_embedding, validation_embedding)

        classifier = Dense(1, activation='sigmoid')(distances)

        return Model(inputs=[input_image, validation_image],
                    outputs=classifier,
                    name='FinalModel')
    def get_model(self):
        return self.model


