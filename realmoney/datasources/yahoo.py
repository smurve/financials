import datetime as dt
import requests
from io import StringIO
import pandas as pd

class YahooResource:
    
    def ohlcav(self, symbol, from_, to_):

        if isinstance(from_, dt.date):
            from_ = int(dt.datetime(from_.year, from_.month, from_.day, 0).timestamp())        
        if isinstance(to_, dt.date):
            to_ = int(dt.datetime(to_.year, to_.month, to_.day, 0).timestamp())        
        """
        Returns open/high/low/close/adjusted/volume in a dataframe
        """
        url=f"https://query1.finance.yahoo.com/v7/finance/download/{symbol}?" + \
            f"period1={from_}&period2={to_}&interval=1d&includeAdjustedClose=true"  

        res = requests.get(url)

        if res.status_code != 200:
            raise ValueError(f'Failed to download data for {symbol}')

        string = res._content.decode('UTF8')

        df = pd.read_csv(StringIO(string), sep=',')
        
        df['Date'] = df['Date'].apply(lambda d: dt.datetime.strptime(d, "%Y-%m-%d").date())
        
        return df