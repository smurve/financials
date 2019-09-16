import tensorflow as tf
import tensorflow.keras as tk
import tensorflow.keras.layers as tkl


def new_actor(n_market, n_history, n_filters, n_portfolio, activation='relu'):
    inp_mh = tk.Input(shape=[n_history, n_market, 1], dtype=tf.float32)
    inp_pw = tk.Input(shape=[n_portfolio], dtype=tf.float32)

    conv = tkl.Conv2D(activation=None, filters=n_filters, padding='valid',
                    kernel_size=[n_history, 1])
    reshape = tkl.Reshape([n_market*n_filters])
    concat = tkl.Concatenate(axis=-1)
    hidden1 = tkl.Dense(units=16, activation='relu')
    hidden2= tkl.Dense(units=16, activation='relu')
    out = tkl.Dense(units=n_portfolio, activation='softmax')
    outputs = out(
        #hidden2(
        #    hidden1(
                concat(
                    [reshape(conv(inp_mh)), inp_pw]
         #       )
         #   )
        )
    )
    model = tk.Model([inp_mh, inp_pw], outputs)
    model.n_history=n_history
    model.n_market=n_market
    model.n_portfolio=n_portfolio
    return model


def new_critic(n_market, n_history, n_filters, n_portfolio, activation='relu'):   
    inp_mh = tk.Input(shape=[n_history, n_market, 1], dtype=tf.float32)
    inp_pw = tk.Input(shape=[n_portfolio], dtype=tf.float32)    
    inp_pa = tk.Input(shape=[n_portfolio], dtype=tf.float32)    
    
    conv = tkl.Conv2D(activation=None, filters=n_filters, padding='valid',
                    kernel_size=[n_history, 1])
    reshape = tkl.Reshape([n_market*n_filters])
    concat = tkl.Concatenate(axis=-1)
    hidden1 = tkl.Dense(units=16, activation='relu')
    hidden2 = tkl.Dense(units=8, activation='relu')
    out = tkl.Dense(units=1, activation='tanh')
    outputs = out(
        #hidden2(hidden1(
            concat(
                [reshape(conv(inp_mh)), inp_pw, inp_pa]
            )
        #))
    )
    model = tk.Model(inputs=[inp_mh, inp_pw, inp_pa], outputs=outputs)
    model.n_history=n_history
    model.n_market=n_market
    model.n_portfolio=n_portfolio
    return model

