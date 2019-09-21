import numpy as np
import tensorflow as tf
import tensorflow.keras as tk
import tensorflow.keras.layers as tkl

def SINX(x):
    x1=x+3*np.sin(x/5.5)
    return 10 + np.sin(x1/10) + np.sin(x1/33) + np.sin(x1/100)


def COSX(x):
    x2=0.7*x+2*np.cos(x/5.5)
    return 12 + np.cos(x2/10) - np.cos(x2/23) + np.cos(x2/100)


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

class Observation():
    def __init__(self, s, a, r, s1):
        self.s = s
        self.a = a
        self.r = r
        self.s1 = s1
        
    def __repr__(self):
        return str([self.s, self.a, self.r, self.s1])
    
    
def arrange (batch):
    N_BATCH=len(batch)
    # s
    mh = np.array([batch[i].s[0] for i in range(N_BATCH)])
    pw = np.array([batch[i].s[1] for i in range(N_BATCH)])

    # a 
    a = np.array([batch[i].a for i in range(N_BATCH)])

    # r
    r = np.array([batch[i].r for i in range(N_BATCH)]).reshape(N_BATCH, 1)

    # s1
    mh1 = np.array([batch[i].s1[0] for i in range(N_BATCH)])
    pw1 = np.array([batch[i].s1[1] for i in range(N_BATCH)])    
    
    return mh, pw, a, r, mh1, pw1



class Environment():
    def __init__(self, n_hist, portfolio, fee=2e-3):
        self.n_hist = n_hist
        self.t = n_hist
        self.portfolio = np.array(portfolio)
        self.fee = fee
        self.total_fees=0
        self.initial_wealth = np.sum(portfolio)
  
    def SINX(self, x):
        x1=x+3*np.sin(x/5.5)
        return (10 + np.sin(x1/10) + np.sin(x1/33) + np.sin(x1/100)).astype(np.float32)

    def COSX(self, x):
        x2=0.7*x+2*np.cos(x/5.5)
        return (12 + np.cos(x2/10) - np.cos(x2/23) + np.cos(x2/100)).astype(np.float32)
    
    def market_history(self):
        return np.array([[self.SINX(x), self.COSX(x)] 
                         for x in range(self.t-self.n_hist, self.t)])

    def log_return_history(self):
        h = np.array([[self.SINX(x), self.COSX(x)] 
                         for x in range(self.t-self.n_hist-1, self.t)])
        return np.array(
            [np.log(h[1:,0] / h[:-1,0]),
             np.log(h[1:,1] / h[:-1,1])]).T

        
    def state(self):
        return (self.log_return_history(), self.normalized_holdings())
    
    def step(self, newp):        
        s = (self.log_return_history(), self.normalized_holdings())
        a = np.array(newp).astype(np.float32)
        self.rebalance(newp)
        w = self.wealth()
        self.tick()
        r = np.log(self.wealth()/w)
        s1 = (self.log_return_history(), self.normalized_holdings())
        return Observation(s,a,r,s1)

    def cash(self):
        return self.portfolio[0]
    
    def wealth(self):
        return np.sum(self.portfolio)
    
    def normalized_holdings(self):
        return (self.portfolio / self.initial_wealth).astype(np.float32)

    def rebalance(self, newp):
        newp = np.array(newp) * self.wealth()
        tx = np.sum(np.abs(self.portfolio - newp))
        self.portfolio = newp
        cost = tx * self.fee
        self.portfolio[0] -= cost
        self.total_fees = round(self.total_fees + cost, 2)
        return self
    
    def tick(self):
        self.portfolio[1] *= SINX(self.t+1) / SINX(self.t)
        self.portfolio[2] *= COSX(self.t+1) / COSX(self.t)
        self.t += 1
        return self
    
    def __repr__(self):
        return "wealth: %s, portfolio: %s" % (
            np.round(self.wealth(), 2), np.round(self.portfolio, 2))