import numpy as np
from stockmarket import Investor, Bid, Ask

class MomentumInvestor(Investor):
    """
    A momentum investor who has some reasoning wrt true value
    """
    def __init__(self, name, wealth, portfolio, w_reason = 0.5, w_momentum = 0.5, trend_span=20):
        self.w_reason = w_reason
        self.w_momentum = w_momentum
        self.trend_span = trend_span
        self.history = []
        super().__init__(name, wealth, portfolio)
        
    def act(self, market):
        for ticker in market.prices:
            self.act_on(market, ticker)
        
    def act_on(self, market, ticker):
            bid, ask = market.price_for(ticker)
            h = market.history_for(ticker)
            h = h[-self.trend_span:]
            bid_price, ask_price = market.price_for(ticker)
            if len(h) > 0:
                # comparing opening prices
                N_TX = 10
                momentum = np.log(h[-1][0] / h[0][0])
                value_diff = np.log(market.value_for(ticker) / bid_price)
                incentive = value_diff * self.w_reason + momentum * self.w_momentum
                incentive = np.random.normal(incentive, .2)
                self.history.append([value_diff, momentum, incentive])
                if incentive > 0:
                    if ( self.cash > N_TX * bid_price + 1000.0):
                        market.execute(Bid(self, ticker, N_TX, bid_price))
                else:
                    if self.portfolio[ticker] >= N_TX:
                        market.execute(Ask(self, ticker, N_TX, ask_price))

                
class ValueInvestor(Investor):
    def __init__(self, name, wealth, portfolio):
        super().__init__(name, wealth, portfolio)

    def act(self, market):
        active = False
        bid, ask = market.price_for('AAPL')
        return active
        
            
class SignalInvestor(Investor):
    def __init__(self, name, wealth, portfolio):
        super().__init__(name, wealth, portfolio)
        
    def act(self, market):
        bid, ask = market.price_for('AAPL')

        
