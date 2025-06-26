from tensorflow.keras.layers import Layer
import tensorflow as tf

class L1Dist(Layer):
    """L1 Distance Layer for calculating Manhattan Distance"""
    def __init__(self, **kwargs):
        super().__init__()
    def call(self, input_embedding, validation_embedding):
        return tf.math.abs(input_embedding - validation_embedding)

class L2Dist(Layer):
    """L2 Distance Layer for calculating Enclidian Distance"""
    def __init__(self, **kwargs):
        super().__init__()
    def call(self, input_embedding, validation_embedding):
        return tf.sqrt(tf.reduce_sum(tf.square(input_embedding - validation_embedding), axis=1, keepdims=True))