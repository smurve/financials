import numpy as np
from stockmarket import Market, Investor
from investors import MomentumInvestor

sectors = {
    10: {"name": "Energy", "weight": .09, "cagr": .02, "sentiment": .1},
    15: {"name": "Materials", "weight": .09, "cagr": .02, "sentiment": .1},
    20: {"name": "Industrials", "weight": .09, "cagr": .02, "sentiment": .1},
    25: {"name": "Consumer Discretionary", "weight": .09, "cagr": .02, "sentiment": .1},
    30: {"name": "Consumer Staples", "weight": .09, "cagr": .02, "sentiment": .1},
    35: {"name": "Healthcare", "weight": .09, "cagr": .02, "sentiment": .1},
    40: {"name": "Financials", "weight": .09, "cagr": .02, "sentiment": .1},
    45: {"name": "Information Technology", "weight": .1, "cagr": .02, "sentiment": .1},
    50: {"name": "Communication Services", "weight": .09, "cagr": .02, "sentiment": .1},
    55: {"name": "Utilities", "weight": .09, "cagr": .02, "sentiment": .1},
    60: {"name": "Real Estate", "weight": .09, "cagr": .02, "sentiment": .1}
}

markets = { 
    1: {'name': 'US', "weight": .2, "cagr": .3, "sentiment": .1},
    2: {'name': 'Europe', "weight": .16, "cagr": .3, "sentiment": .1},
    3: {'name': 'South America', "weight": .16, "cagr": .3, "sentiment": .1},
    4: {'name': 'China', "weight": .16, "cagr": .3, "sentiment": .1},
    5: {'name': 'Oceania', "weight": .16, "cagr": .3, "sentiment": .1},
    6: {'name': 'Asia', "weight": .16, "cagr": .3, "sentiment": .1}
}


class Trending:
    def __init__(self, name, sentiments):
        """
        Parameters:
        sentiments: A map {t_i: (a_i, b_i)} that defines the discontinuous piecewise
        linear sentiment function. See implementation of phi(t) to understand.
        """
        self.name = name
        self.sentiments = sentiments
        
    def phi(self, t):
        periods = sorted(self.sentiments.items())
        current_period = 0
        for p in periods:
            if p[0] > t: 
                break
            else:
                current_period = p
        t0, (alpha, beta) = current_period
        return alpha + (t-t0) * beta
    
    
    
class Stock(Trending):
    def __init__(self, name, psi0, E_cagr, sentiments, max_effect,
                 noise, segments={}, markets={}, days_per_year=256):
        """
        Parameters: 
        psi0: the initial average perceived value of the stock
        E_cagr: the expacted compound annual growth rate for constant neutral sentiment
        sentiments: A map of periods - see class Trending
        max_effect: the maximum multiplier to the true value that the sentiment can achieve
        segments: map of segments as keys and their weights (adding up to 1.0)
        """
        super(Stock, self).__init__(name, sentiments)
        self.days_per_year = days_per_year
        self.psi0 = psi0
        self.nu = nu = np.log(1+E_cagr)
        self.max_effect = max_effect
        self.noise = noise
        self.segments = segments
        self.markets = markets
        
    def value(self, t):
        return np.random.normal(self.psi(t), self.noise)
        
    def psi(self,t):
        """
        the total sentiment score from all geomarket exposures and segments
        """
        
        def sentiment_effect(x):
            K = self.max_effect
            delta = np.log(K-1)
            return K / (1 + np.exp(-x + delta))         

        sentiment = self.phi(t) + (
            np.sum([s[1] * s[0].phi(t) for s in self.segments.items()]) +
            np.sum([m[1] * m[0].phi(t) for m in self.markets.items()]))
        
        return self.psi0 * np.exp(t/self.days_per_year*self.nu) * sentiment_effect(sentiment)
        
        
        
class GeoMarket(Trending):
    def __init__(self, name, sentiments):
        super(GeoMarket, self).__init__(name, sentiments)
        
class Segment(Trending):
    def __init__(self, name, sentiments):
        super(Segment, self).__init__(name, sentiments)
    

## Geo markets

# A bullish year followed by a bearish one
us = GeoMarket('US', {0: (.1,0), 360: (-.6, 0)})
# Obviously, the trade war is ongoing
china = GeoMarket('China', {0: (-.1,0), 360: (.2, 0)})
# Europe is stable
europe = GeoMarket('Europe', {0: (.2,0), 360: (.2, 0)})



## Segments

# IT has come to a saturation and disappointment phase
it = Segment('Information Technology', {0: (-.1, 0)})
# Industry
industrials = Segment('Industrials', {0: (-.1, 0)})


# Two years' sentiment scores

aapl_sentiments = {
    0: (1, 0),         # start bullish for the first 90 days 
    90: (.5, .5/90),   # cool down a bit but recover well
    180: (-1, 1/90),   # bad earnings, still recovering well
    360: (.4, 0),      # good sentiment
    450: (.3, 0),
    540: (.6, 0),
    630: (0, -1/180),
    720: (0, 0)}  # initially neutral sentiment - decreasing

msft_sentiments = {
    0: (.1, 0),       
    90: (.2, .5/90),  
    180: (.1, 1/90),  
    360: (-.1, 0),    
    450: (.2, 0),
    540: (.1, 0),
    630: (0, -1/180),
    720: (0, 0)}  

tsla_sentiments = {
    0: (.1, 0),       
    90: (-.2, .1/90),  
    180: (.1, -1/90),  
    360: (-.1, 0),    
    450: (.2, 0),
    540: (-.1, 0),
    630: (0, -1/180),
    720: (0, 0)}  


aapl = Stock(name='AAPL', psi0=100, E_cagr=0.05, max_effect=2.0,
             segments = {it: 1.0}, 
             markets={us: 0.5, europe: .3, china: 0.2},
             sentiments=aapl_sentiments, noise=2.0)

msft = Stock(name='MSFT', psi0=200, E_cagr=0.03, max_effect=2.0,
             segments = {it: 1.0}, 
             markets={us: .5, europe: .4, china: .1},
             sentiments=msft_sentiments, noise=2.0)

tsla = Stock(name='TSLA', psi0=150, E_cagr=0.06, max_effect=2.0,
             segments = {industrials: 1.0}, 
             markets={us: .4, europe: .6, china: 0},
             sentiments=tsla_sentiments, noise=2.0)


def new_market(): 
    return Market(stocks=[aapl, msft, tsla], bid_ask=0.1)

def make_investors(num_investors, portfolio=None):
    from copy import deepcopy
    investors = []
    for i in range(num_investors):
        wr, wm, span = 0.3, 0.15, 20
        portfolio = deepcopy(portfolio) or {'AAPL': 10000, 'TSLA': 10000, 'MSFT': 10000}
        investor = MomentumInvestor("m-%s" % i, 1e8, portfolio, wr, wm, span)
        investors.append(investor)
    return investors