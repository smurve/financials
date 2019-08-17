import tensorflow as tf

class LSTM_TraderModel(tf.keras.Model):
    def __init__(self, n_neurons, n_steps, n_features, n_out):
        super(LSTM_TraderModel, self).__init__()
        self.lstm = tf.keras.layers.LSTM(
            n_neurons, 
            input_shape=[None, n_steps, n_features],
            return_sequences=False)
        self.logits = tf.keras.layers.Dense(n_out, activation = None)
        
    def call(self, inputs):
        out = tf.cast(inputs, dtype=tf.float32)
        out = self.lstm(out) 
        out = self.logits(out)
        return out
    
    def portfolio(self, inputs):
        return tf.keras.activations.softmax(self.call(inputs))

