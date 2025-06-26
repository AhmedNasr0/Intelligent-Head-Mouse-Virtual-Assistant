
import tensorflow as tf

class CustomWeightInitializer(tf.keras.initializers.Initializer):
    def __call__(self, shape, dtype=None):
        return tf.random.normal(shape, mean=0.0, stddev=1e-2, dtype=dtype)

class CustomBiasInitializer(tf.keras.initializers.Initializer):
    def __call__(self, shape, dtype=None):
        return tf.random.normal(shape, mean=0.5, stddev=1e-2, dtype=dtype)