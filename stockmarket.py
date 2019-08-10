import numpy as np
import uuid
import math
import operator

class Stock:
    def __init__(self, name, trend_fun, noise):
        """
        name: Name of the stock
        trend_fun: a 'true' value function mimicking fundamentals.
        noise: noise to model the uncertainty of the 'true' value
        """
        self.name = name
        self.trend = trend_fun
        self.noise = noise
        
    def value(self, t):
        """
        true value plus noise
        """
        v = self.trend(t)
        return np.random.normal(v, self.noise)
        
        
class Order:
    def __init__(self, tx, other_party, ticker, amount, price):
        self.order_id = uuid.uuid4().hex
        self.tx = tx
        self.other_party = other_party
        self.ticker = ticker
        self.amount = amount
        self.price = price
        
    def __repr__(self):
        return self.other_party.name + ":" + self.ticker + ":" + str(self.amount) + ":" + str(self.price)

class Bid(Order):
    def __init__(self, other_party, ticker, amount, price):
        super().__init__('bid', other_party, ticker, amount, price)
        
class Ask(Order):
    def __init__(self, other_party, ticker, amount, price):
        super().__init__('ask', other_party, ticker, amount, price)

class OrderStatus():
    
    DEFERED = 'DEFERED'
    EXECUTED = 'EXECUTED'
    IGNORED = 'IGNORED'
    
    def __init__(self, order_id, status):
        self.order_id = order_id
        self.status = status
        
    def is_defered(self):
        return self.status == OrderStatus.DEFERED
    
    def is_executed(self):
        return self.status == OrderStatus.EXECUTED
    
    def is_ignored(self):
        return self.status == OrderStatus.IGNORED
        
class OrderExecuted(OrderStatus):
    def __init__(self, order, price):
        super().__init__(order.order_id, OrderStatus.EXECUTED)
        self.tx_price = price

class OrderIgnored(OrderStatus):
    def __init__(self, order):
        super().__init__(order.order_id, OrderStatus.IGNORED)
        
class OrderDefered(OrderStatus):
    def __init__(self, order):
        super().__init__(order.order_id, OrderStatus.DEFERED)

    
class Market:
    def __init__(self, stocks=None):
        self.t = 0
        self.orders = {
            'ask': {},
            'bid': {}
        }
        self.prices = {}
        
        self.spread = .1
        self.history={}
        
        self.stocks = {}
        if stocks:
            for stock in stocks:
                self.stocks[stock.name] = stock
                self.orders['ask'][stock.name] = {} 
                self.orders['bid'][stock.name] = {} 
                self.prices[stock.name] = round(stock.value(0), 3)
                self.history[stock.name] = []
        
    def tick(self):
        """
        create another tick without a transaction
        """
        self.t += 1
        for ticker in self.prices:
            self.history[ticker].append(self.prices[ticker])
        
        
    def tx_price(self, ticker, tx):
        delta = self.spread if tx == 'bid' else -self.spread
        return round(self.prices[ticker] + delta, 3)

    
    def execute (self, order, defer=True, reprocessing=False):
                    
        # bid-ask spread
        tx_price = self.tx_price(order.ticker, order.tx)
        
        # If we have an immediate match
        if (order.price >= tx_price and order.tx == 'bid') or (order.price <= tx_price and order.tx == 'ask'):
            #print("Executing order %s" % order.order_id)
            if (order.tx == 'bid'):
                order.other_party.buy(order.ticker, order.amount, tx_price)
            else:
                order.other_party.sell(order.ticker, order.amount, tx_price)

            # Compute new price - only for original orders, not for deferred ones
            if not reprocessing:
                self.prices[order.ticker] = tx_price
                self.t += 1
                self.history[order.ticker].append(tx_price)
                
            status = self.maybe_process_defered('ask' if order.tx == 'bid' else 'bid', order.ticker)

            return OrderExecuted(order, tx_price)
        
        else:
            if defer:
                self.tick()
                #print("Defering order %s" % order.order_id)
                self.orders[order.tx][order.ticker][order.order_id]=order
                return OrderDefered(order)
                    
        return OrderIgnored(order)
        

    def remove_order(self, order):
        tx, ticker, order_id = order.tx, order.ticker, order.order_id
        del(self.orders[tx][ticker][order_id])

        
    def maybe_process_defered(self, tx, ticker):
        order_ids = list(self.orders[tx][ticker].keys())
        last_status = None
        for order_id in order_ids:
            #print("checking order: %s" % order_id)
            order = self.orders[tx][ticker][order_id]
            status = self.execute(order, defer=True, reprocessing=True)
            last_status = status
            if status.is_executed():
                self.remove_order(order)
        return last_status
            
        
    def price_for(self, ticker):
        return self.tx_price(ticker, 'bid'), self.tx_price(ticker, 'ask')

    
    def value_for(self, ticker):
        return self.stocks[ticker].value(self.t)
    
    def history_for(self, ticker):
        return list(self.history[ticker])
    
    
class Investor:
    def __init__(self, name, wealth):
        self.wealth = wealth
        self.name = name
        self.portfolio = {'AAPL': 200}
    
    def sell(self, symbol, n, p):
        self.wealth += n * p
        pos = self.portfolio[symbol]
        self.portfolio[symbol] = pos - n
        
    def buy(self, symbol, n, p):
        self.wealth -= n * p
        pos = self.portfolio[symbol]
        self.portfolio[symbol] = pos + n
       
    def __repr__(self):
        return self.name + "(" + str(self.wealth) + ", " + str(self.portfolio['AAPL'])+ ")"
               
