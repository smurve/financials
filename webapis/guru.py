import pandas as pd
import numpy as np
import json
from urllib.request import Request, urlopen


class Guru:
    
    def __init__(self, key):
        self.key = key

    def prices(self, stock):
        subject='price'
        api_key = '73142da8657cc5dfa541b546d1560131:4886c27790bc76bd5e076340a403ade5'
        url = 'https://api.gurufocus.com/public/user/%s/stock/%s/%s' % (self.key, stock, subject)
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urlopen(req)
        content = response.read()
        data = json.loads(content.decode('utf8'))
        return data
    
    def prices_pd (self, ticker):
        col_name = ticker
        data = self.prices(ticker)
        ts = pd.DataFrame(data, columns=(['Date', col_name]))
        dates = pd.to_datetime(ts['Date'],format='%m-%d-%Y')
        ts['Date'] = dates
        ts.set_index('Date', inplace=True)
        ts[col_name] = ts[col_name].astype(float)
        return ts
    
    def charts(self, tickers):
        charts = self.prices_pd(tickers[0])
        for ticker in tickers: 
            charts[ticker] = self.prices_pd(ticker)
        return charts
    
    def financials(self, stock):
        url = 'https://api.gurufocus.com/public/user/%s/stock/%s/financials' % (self.key, stock)
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urlopen(req)
        content = response.read()
        data = json.loads(content.decode('utf8'))
        return data['financials']
    
    def quarterly(self, stock, key):
        data = self.financials(stock)
        fy = data['quarterly']['Fiscal Year']
        source=pd.DataFrame(data['quarterly'][key])
        source['Fiscal Year'] = fy
        source.set_index('Fiscal Year', inplace=True)
        source = source.astype(float)
        return source
    
    @staticmethod
    def growth_multiple(growth):
        """
        Heuristic from gurufocus
        params: growth: a number between 4 and 15
        """
        return 8.3459 * 1.07 ** (growth - 4.0)
    
    @staticmethod
    def dataframe_from (data_dict, doc_id, frequency='quarterly'):
        dates = data_dict[frequency]['Fiscal Year']
        dates = [date+"-28" for date in dates]

        df = pd.DataFrame(dates, columns=(['Date']))

        doc = data_dict[frequency][doc_id]
        for key in doc:
            try: 
                df[key] = np.array(doc[key]).astype(float)
            except:
                pass # fails with Debt-to-Equity value 'N/A' - we don't need it

        df['Date'] = pd.to_datetime(df['Date'],format='%Y-%m-%d')
        df.set_index('Date', inplace=True)
        return df    
    
    def balance_sheet(self, financials):
        df = Guru.dataframe_from(financials, 'balance_sheet')
        df['Total Equity'] = df['Total Assets'] - df['Total Liabilities']
        return df    

    def valuation_and_quality(self, financials):
        df = Guru.dataframe_from(financials, 'valuation_and_quality')
        return df    

    def cashflow_statement(self, financials):
        df = Guru.dataframe_from(financials, 'cashflow_statement')
        # 6 year moving avg for intrinsic value calculations
        df['FCF 6y avg'] = df['Free Cash Flow'].rolling("2190d").sum() / 6  
        return df    
    
    def adjusted_fair_value(self, symbol, adjustment):

        prices = self.prices_pd(symbol)

        financials=self.financials(symbol)
        cfs = self.cashflow_statement(financials)
        bs = self.balance_sheet(financials)
        
        # This is naively assuming positive total equity.
        cfs['Fair Value'] =  0.8 * bs['Total Equity'] + Guru.growth_multiple(8) * cfs['FCF 6y avg']

        shares_outstanding = financials['quarterly']\
            ['valuation_and_quality']\
            ['Shares Outstanding (Basic Average)']
        
        shares_outstanding = np.array(shares_outstanding).astype(float)

        cfs['Fair Value'] /= shares_outstanding

        prices['Fair Value (adj)'] = cfs['Fair Value'] * adjustment
        
        #val = 0.
        #for i in range(len(prices)):
        #    if prices['Fair Value (adj)'].iloc[i] > 0:
        #        val = prices['Fair Value (adj)'].iloc[i]
        #    else:
        #        prices['Fair Value (adj)'].iloc[i] = val

        vnq = self.valuation_and_quality(financials)                
        prices['Peter Lynch Fair Value'] = vnq['Peter Lynch Fair Value']
        prices['Intrinsic Value: Projected FCF'] = vnq['Intrinsic Value: Projected FCF']
        self.cont_nan(prices)
        return prices[[symbol, 'Fair Value (adj)', 'Intrinsic Value: Projected FCF',
                       'Peter Lynch Fair Value']];
    
    
    def cont_nan(self, df):
        """
        replace all np.nans with the most recent valid number in that series
        """
        for column in df.columns:
            val = 0.
            for i in range(len(df)):
                if df[column].iloc[i] > 0:
                    val = df[column].iloc[i]
                else:
                    df[column].iloc[i] = val

