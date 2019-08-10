import numpy as np
from stockmarket import Investor, Bid, Ask

class MomentumInvestor(Investor):
    """
    A momentum investor who has some reasoning wrt true value
    """
    def __init__(self, name, wealth, w_reason = 0.5, w_momentum = 0.5, trend_span=20):
        self.w_reason = w_reason
        self.w_momentum = w_momentum
        self.trend_span = trend_span
        super().__init__(name, wealth)
        
    def act(self, market):
            bid, ask = market.price_for('AAPL')
            h = market.history_for('AAPL')
            h = h[-self.trend_span:]
            bid_price, ask_price = market.price_for('AAPL')
            if len(h) > 0:
                momentum = h[-1] - h[0]
                value_diff = market.value_for('AAPL') - bid_price
                incentive = value_diff * self.w_reason + momentum * self.w_momentum
                incentive = np.random.normal(incentive, 2.0)
                #print("Value difference: %s" % value_diff )
                #print("momentum:         %s" % momentum)
                #print("Incentive: %s" % incentive)
                if incentive > 0:
                    #print("Buying at %s" % bid_price)
                    market.execute(Bid(self, 'AAPL', 10, bid_price))
                else:
                    #print("Selling at %s" % ask_price)
                    market.execute(Ask(self, 'AAPL', 10, ask_price))
            else:
                market.execute(Ask(self, 'AAPL', 10, ask_price))

                
class ValueInvestor(Investor):
    def __init__(self, name, wealth):
        super().__init__(name, wealth)

    def act(self, market):
        active = False
        bid, ask = market.price_for('AAPL')
        return active
        
            
class SignalInvestor(Investor):
    def __init__(self, name, wealth):
        super().__init__(name, wealth)
        
    def act(self, market):
        bid, ask = market.price_for('AAPL')

        
