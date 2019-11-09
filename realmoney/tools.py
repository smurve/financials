from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import datetime
import quandl

class Forex:
    """
    Wrapper that scrapes from currency-converter.org.uk
    """
    def __init__(self, currencies):
    
        self.forex = {}
        for cfrom in currencies:
            for cto in currencies:
                if cfrom != cto:
                    url=('https://www.currency-converter.org.uk/currency-rates'+
                         '/historical/table/%s-%s.html' % (cfrom, cto))
                    page = urlopen(url)
                    soup = BeautifulSoup(page, features="lxml")

                    rows = soup.find(text='Friday').parent.parent.parent.findChildren('tr')[1:-1]

                    rates = [[row.findChildren('td')[1].text, 
                              float(row.findChildren('td')[3].text.split(" ")[0])] for row in rows]

                    fx = pd.DataFrame(rates, columns=['Date', '1%s=%s' % (cfrom, cto)])
                    fx.Date = pd.to_datetime(fx.Date, format="%d/%m/%Y")
                    fx.set_index('Date', inplace=True)
                    self.forex['%s-%s' % (cfrom, cto)] = fx

    def rates_for(self, cfrom, cto):
        return self.forex['%s-%s' % (cfrom, cto)]
                    
    def rate_for(self, cfrom, cto, date): 
        key = '1%s=%s' % (cfrom, cto)
        f =  self.forex["%s-%s" % (cfrom, cto)]
        rate = f[key].where(f.index == date).dropna().iloc[0]
        return rate
    
    
def read_tx_efinance(filename):
    df = pd.read_csv(filename, encoding='iso8859_2', delimiter=';')
    df.Nettobetrag = df.Nettobetrag.map(lambda x: float(str(x).replace("'", "")))
    df.Stückpreis = df.Stückpreis.map(lambda x: float(str(x).replace("'", "")))
    df.Saldo = df.Saldo.map(lambda x: float(str(x).replace("'", "")))
    del df['ISIN']
    del df["Auftrag #"]
    del df["Nettobetrag in der Währung des Kontos"]
    df.Name.replace(np.nan, "-", inplace=True, regex=True)
    df['Time'] = pd.to_datetime(df.Datum, format='%d-%m-%Y %H:%M:%S')
    df.Datum = pd.to_datetime(df.Datum.map(lambda x: x.split(" ")[0]), format='%d-%m-%Y')
    df.rename(columns={'Datum': 'Date'}, inplace=True)
    df.drop(['Aufgelaufene Zinsen', 'Name'], axis=1, inplace=True)
    #df.set_index('Date', inplace=True)
    return df

def merge_by_date_index(df1, df2, how='inner'):
    df = pd.merge(df1, df2, left_on=df1['Date'], 
                  right_on=df2.index, how=how)
    del df['Date']
    df.rename(columns={'key_0': 'Date'}, inplace=True)
    return df

def next_day(date):
    return datetime.datetime.fromordinal(date.toordinal()+1)


class PortfolioManager:

    import quandl
    import datetime

    def __init__(self, initial_amount, tx_file, special_prices=None):

        self.txdf = read_tx_efinance(tx_file)
        self.symbols = self.txdf.Symbol.dropna().unique()        

        print("Getting price data from quandl...")
        prices = {}
        for symbol in self.symbols:
            if symbol not in special_prices:
                prices[symbol] = quandl.get('EOD/%s' % symbol, start_date='2019-09-01')
                prices[symbol] = prices[symbol][['Adj_Low', 'Adj_High', 'Adj_Close']]
                prices[symbol].columns=['%s Low' % symbol, '%s High' % symbol, '%s Close' % symbol]        
                self.txdf = merge_by_date_index(self.txdf, prices[symbol], how='inner')

        print("Getting forex data for USD/CHF")
        self.forex = Forex(['USD', 'CHF'])                
                
        ### Prices that can't be found on quandl can be assigned a constant price here
        if special_prices:
            self.special_prices = special_prices
            for symbol in special_prices:
                self.txdf[symbol + ' Close'] = len(self.txdf) * [special_prices[symbol]]

        self.actions = {'Kauf': self.buy_shares, 
                        'Verkauf': self.sell_shares, 
                        'Einzahlung': self.einzahlung, 
                        'Fx-Belastung Comp.': self.fx_related,
                        'Fx-Gutschrift Comp.': self.fx_related,
                        'Berichtigung Börsengeb.': self.fx_related}
        
        # first portfolio record one day before the first transaction
        start_date = self.txdf.Date.iloc[-1].to_pydatetime()
        start_date = datetime.datetime.fromordinal(start_date.toordinal()-1)
        
        self.portfolio_history = {start_date: self.initial_portfolio(initial_amount)}
        
        self.calc_portfolio_history()
        
    def initial_portfolio(self, initial_amount):
        einzahlungen = self.txdf.Nettobetrag[self.txdf.Transaktionen == 'Einzahlung'].sum()
        snapshot = {key: 0. for key in (['Giro', 'CHF', 'USD'] + list(self.symbols)) }
        snapshot['CHF'] = initial_amount
        snapshot['networth'] = einzahlungen + initial_amount
        snapshot['Giro'] = einzahlungen
        return snapshot
        

    def share_price(self, symbol, date):
        return self.txdf[self.txdf.Date==date].iloc[0][symbol + " Close"]

    def calc_networth(self, date, pr):

        usd_chf = self.forex.rate_for('USD', 'CHF', date)

        networth = (
            pr['Giro'] + pr['CHF'] + 
            np.sum([self.share_price(symbol, date) * pr[symbol] * usd_chf 
                    for symbol in self.symbols]) +
            pr['USD'] * usd_chf
        )
        pr['networth'] = networth
        return networth
    
    
    def calc_portfolio_history(self):
        for i in range(len(self.txdf)-1, -1, -1):
            record = self.txdf.iloc[i]
            tx = record.Transaktionen
            action = self.actions.get(tx)
            if action:
                action(record)
            else:
                raise Exception("No such action")
                
                
    def buy_shares(self, record):

        last_date, last_record = sorted(self.portfolio_history.items())[-1]
        record_date = record.Date.to_pydatetime()

        if record_date != last_date:
            new_record = last_record.copy()
        else:
            new_record = last_record

        symbol = record.Symbol
        num_shares = record.Anzahl
        price = record.Stückpreis
        curr_tx = record['Währung Nettobetrag']
        curr = record.Währung

        new_record[symbol] += num_shares
        new_record[curr] = record.Saldo

        self.calc_networth(record_date, new_record)
        self.portfolio_history[record_date] = new_record

        
    def sell_shares(self, record):
    
        last_date, last_record = sorted(self.portfolio_history.items())[-1]
        record_date = record.Date.to_pydatetime()

        if record_date != last_date:
            new_record = last_record.copy()
        else:
            new_record = last_record

        symbol = record.Symbol
        num_shares = record.Anzahl
        price = record.Stückpreis
        curr_tx = record['Währung Nettobetrag']
        curr = record.Währung

        new_record[symbol] -= num_shares
        new_record[curr] = record.Saldo 

        self.calc_networth(record_date, new_record)
        self.portfolio_history[record_date] = new_record
        
        
    def einzahlung(self, record):
        last_date, last_record = sorted(self.portfolio_history.items())[-1]
        record_date = record.Date.to_pydatetime()

        if record_date != last_date:
            new_record = last_record.copy()
        else:
            new_record = last_record

        amount = record.Stückpreis

        new_record['Giro'] -= amount

        new_record['CHF'] = record.Saldo 

        self.calc_networth(record_date, new_record)
        self.portfolio_history[record_date] = new_record
        
        
    def fx_related(self, record):
        last_date, last_record = sorted(self.portfolio_history.items())[-1]
        record_date = record.Date.to_pydatetime()

        if record_date != last_date:
            new_record = last_record.copy()
        else:
            new_record = last_record

        curr = record.Währung

        new_record[curr] = record.Saldo 

        self.calc_networth(record_date, new_record)
        self.portfolio_history[record_date] = new_record