import tensorflow as tf
import tensorflow.keras as tk
import tensorflow.keras.layers as tkl


def new_actor(n_market, n_history, n_lstm, hiddens, n_portfolio):
    
    inp_mh = tk.Input(shape=[n_history, n_market], dtype=tf.float32)
    inp_pw = tk.Input(shape=[n_portfolio], dtype=tf.float32)    
    
    # First, compute the influence of the market history
    res = tkl.LSTM(units=n_lstm, return_sequences=False)(inp_mh)
    res = tkl.Dense(units=n_portfolio, activation='softmax')(res)

    # Then, take the current portfolio into consideration
    res = tf.concat([res, inp_pw], axis=-1)   
    for h in hiddens:
        res = tkl.Dense(h, activation='relu')(res)
    res = tkl.Dense(n_portfolio, activation='softmax')(res)
    
    return tk.Model(inputs=[inp_mh, inp_pw], outputs = res)


def new_critic(n_market, n_history, n_lstm, hiddens, n_portfolio):
    
    inp_mh = tk.Input(shape=[n_history, n_market], dtype=tf.float32)
    inp_pw = tk.Input(shape=[n_portfolio], dtype=tf.float32)    
    inp_pa = tk.Input(shape=[n_portfolio], dtype=tf.float32)    
    
    # First, compute the influence of the market history
    res = tkl.LSTM(units=n_lstm, return_sequences=False)(inp_mh)
    res = tkl.Dense(units=n_portfolio, activation='softmax')(res)

    # Then, take the current portfolio and the actions into consideration
    res = tf.concat([res, inp_pw, inp_pa], axis=-1)   
    for h in hiddens:
        res = tkl.Dense(h, activation='relu')(res)
    res = tkl.Dense(1, activation='tanh')(res)
    
    return tk.Model(inputs=[inp_mh, inp_pw, inp_pa], outputs = res)

