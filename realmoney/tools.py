import collections
import datetime
import datetime as dt
import logging
import math

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from datasources.yahoo import YahooResource

yahoo = YahooResource()

logger = logging.getLogger(__name__)


class Forex:
    """
    Wrapper that scrapes from currency-converter.org.uk
    """
    def __init__(self, currencies):
    
        self.forex = {}
        for cfrom in currencies:
            for cto in currencies:
                if cfrom != cto:
                    url = ('https://www.currency-converter.org.uk/currency-rates' +
                           '/historical/table/%s-%s.html' % (cfrom, cto))
                    page = requests.get(url)
                    soup = BeautifulSoup(page.content, features="html.parser")

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
        f = self.forex["%s-%s" % (cfrom, cto)]
        rate = f[key].where(f.index == date).dropna().iloc[0]
        return rate
    
    
def _float(x: str) -> float:
    try:
        return float(x)
    except ValueError:
        return 0.0


def map_symbol(symbol):
    # Note that on Yahoo, Tokyo Electron is listed in EUR, so while holding TKY we'll incur EUR-USD errors,
    # which I ignore until it becomes an issue
    return 'TKY.BE' if symbol == 'TKY' else symbol


def read_tx_efinance(filename):
    df = pd.read_csv(filename, encoding='iso8859_2', delimiter=';')
    
    df.Nettobetrag = df.Nettobetrag.map(lambda x: _float(str(x).replace("'", "")))

    df.Symbol = df.Symbol.map(map_symbol)

    df.Stückpreis = df.Stückpreis.map(lambda x: _float(str(x).replace("'", "")))  # noqa
    df.Saldo = df.Saldo.map(lambda x: _float(str(x).replace("'", "")))
    del df['ISIN']
    del df["Auftrag #"]

    df.Name.replace(np.nan, "-", inplace=True, regex=True)
    df['Time'] = pd.to_datetime(df.Datum, format='%d-%m-%Y %H:%M:%S')
    df = df.sort_values(by='Time')
    df.Datum = pd.to_datetime(df.Datum.map(lambda x: x.split(" ")[0]), format='%d-%m-%Y')
    df.rename(columns={'Datum': 'Date', "Nettobetrag in der Währung des Kontos": 'True_Net'}, inplace=True)
    df.True_Net = df.True_Net.map(lambda x: _float(str(x).replace("'", "")))
    df.drop(['Aufgelaufene Zinsen', 'Name'], axis=1, inplace=True)
    # df.set_index('Date', inplace=True)
    return df


def merge_by_date_index(df1, df2, how='inner'):
    df = pd.merge(df1, df2, left_on='Date', 
                  right_on='Date', how=how)
    del df['Date']
    df.rename(columns={'key_0': 'Date'}, inplace=True)
    return df


def next_day(date):
    return datetime.datetime.fromordinal(date.toordinal()+1)


def general_credit_or_debit(new_record, transaction, forex=None):
    currency = transaction.Währung
    new_record[currency] = round(new_record[currency] + transaction.True_Net, 2)


def in_out_flow(new_record, transaction, forex):
    currency = transaction.Währung
    if currency != 'CHF':
        rate = forex.rate_for(currency, 'CHF', transaction.Date)
    else:
        rate = 1.0

    new_record[currency] = round(new_record[currency] + transaction.True_Net, 2)
    new_record['Giro'] = round(new_record['Giro'] - transaction.True_Net * rate, 2)


def trade_equity(new_record, transaction, forex=None):

    symbol = transaction.Symbol
    num_shares = transaction.Anzahl
    curr = transaction.Währung

    new_record[curr] = round(new_record[curr] + transaction.True_Net, 2)
    if transaction.True_Net < 0:
        new_record[symbol] += num_shares
    else:
        new_record[symbol] -= num_shares


def trade_forex(new_record, transaction, forex=None):
    curr = transaction.Währung

    new_record[curr] = round(new_record[curr] + transaction.True_Net, 2)


class PortfolioManager:

    def __init__(self, initial_amount, tx_file, from_: dt.date, to_: dt.date):

        txdf = read_tx_efinance(tx_file)
        symbols = [map_symbol(symbol) for symbol in txdf.Symbol.dropna().unique()]

        print("Getting price data from yahoo...")

        symbols_with_data = []
        for symbol in symbols:

            symbol = map_symbol(symbol)

            # if symbol not in special_prices:
            try:
                df1 = yahoo.ohlcav(symbol, from_, to_)
                df1 = df1[['Date', 'Low', 'High', 'Adj Close']]
                df1.columns = ['Date', f'{symbol} Low', f'{symbol} High', f'{symbol} Close']
                df1['Date'] = pd.to_datetime(df1['Date'])
                txdf = pd.merge(txdf, df1, left_on='Date', right_on='Date', how='outer')
                symbols_with_data.append(symbol)
            except ValueError:
                logger.warning(f"Can't get price data for {symbol}")

        self.symbols = symbols_with_data

        self.txdf = txdf[txdf.Transaktionen.notna()]

        logger.info("Getting forex data for USD/CHF")
        self.forex = Forex(['USD', 'CHF'])                
                
        self.actions = {'Kauf': trade_equity,
                        'Verkauf': trade_equity,
                        'Einzahlung': in_out_flow,
                        'Auszahlung': in_out_flow,
                        'Fx-Belastung Comp.': trade_forex,
                        'Fx-Gutschrift Comp.': trade_forex,
                        'Forex-Belastung': trade_forex,
                        'Forex-Gutschrift': trade_forex,
                        'Berichtigung Börsengeb.': general_credit_or_debit,
                        'Jahresgebühr': general_credit_or_debit,
                        'Zins': general_credit_or_debit,
                        'Titeleingang': None,
                        'Titelausgang': None}

        # first portfolio record one day before the first transaction
        start_date = min(self.txdf.Date).to_pydatetime()
        start_date = datetime.datetime.fromordinal(start_date.toordinal()-1)
        
        self.portfolio_history = self.calc_portfolio_history(start_date, initial_amounts={'CHF': initial_amount})
        
    def initial_portfolio(self, initial_amounts):
        einzahlungen = self.txdf.Nettobetrag[self.txdf.Transaktionen == 'Einzahlung'].sum()
        auszahlungen = self.txdf.Nettobetrag[self.txdf.Transaktionen == 'Auszahlung'].sum()
        snapshot = {key: 0. for key in (['Giro', 'CHF', 'USD'] + list(self.symbols))}
        snapshot['CHF'] = initial_amounts['CHF']
        snapshot['networth'] = round(initial_amounts['CHF'] + einzahlungen + auszahlungen, 2)
        snapshot['Giro'] = round(einzahlungen + auszahlungen, 2)
        return snapshot

    def share_price(self, symbol, date):
        """
        return the most recent close price - looking backwards from date.
        """
        while len(self.txdf[self.txdf.Date == date]) == 0 or \
                math.isnan(self.txdf[self.txdf.Date == date].iloc[0][symbol + " Close"]):
            date = date - datetime.timedelta(days=1)
        return self.txdf[self.txdf.Date == date].iloc[0][symbol + " Close"]

    def calc_networth(self, date, pr):

        usd_chf = self.forex.rate_for('USD', 'CHF', date)

        networth = (
            pr['Giro'] + pr['CHF'] + 
            np.sum([self.share_price(symbol, date) * pr[symbol] * usd_chf 
                    for symbol in self.symbols]) +
            pr['USD'] * usd_chf
        )
        networth = round(networth, 2)
        return networth

    def calc_portfolio_history(self, start_date, initial_amounts):
        portfolio_history = collections.OrderedDict()
        portfolio_history[start_date] = self.initial_portfolio(initial_amounts)
        # txdf must be time-ordered!
        previous_record = list(portfolio_history.values())[0]
        last_date = start_date
        for index, transaction in self.txdf.iterrows():

            record_date = transaction.Date.to_pydatetime()

            if record_date != last_date:
                new_record = previous_record.copy()
            else:
                new_record = previous_record

            self.process(new_record, transaction)
            portfolio_history[record_date] = new_record

            last_date = record_date
            previous_record = new_record

        return portfolio_history

    def process(self, new_record, tx):
        record_date = tx.Date.to_pydatetime()
        tx_type = tx.Transaktionen

        execute_booking = self.actions.get(tx_type)
        if execute_booking:
            execute_booking(new_record, tx, forex=self.forex)
            networth = self.calc_networth(record_date, new_record)
            new_record['networth'] = networth
