import pandas as pd
import numpy as np

'''
Add Strategies here using class
'''
class Strategy:
    def __init__(self, ord_type: str, slippage: float, price_data: pd.DataFrame, indicator: pd.DataFrame, param: dict):
        '''
        * The date/timeframe of price data and indicator should be in same scale.

        :param price_data: dataframe where columns are [date, open, high, low, close, volume]
        :param indicator: dataframe where columns are [date, indicator x]
        :param ord_type: MARKET, LIMIT
        :param slippage: stress imposed on each trade (valid for market)
        :param indicator: indicator data
        :param param: dictionary with the names of parameters as keys
        '''
        self.order_t = ord_type
        self.slippage = slippage
        self.data = price_data
        self.indicator = indicator
        self.param = param

    def update_param(self, param_name: str, val):
        self.param.update({param_name: val})
        return self.param

    def generate_signal(self, df):
        pass


class BollingerBandMR(Strategy):
    def __init__(self, ord_type: str, slippage: float, price_data: pd.DataFrame, param: dict, indicator: pd.DataFrame):
        super().__init__(ord_type, slippage, price_data, indicator, param)

    def generate_signal(self, input_df:pd.DataFrame):
        '''
        :param df: columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'indicator']
        :return: dataframe with signals
        '''
        window = self.param['window']
        upper_sig = self.param['upper_sig']
        lower_sig = self.param['lower_sig']
        df = input_df.copy()

        # change the name of indicator columns to sth general
        df.columns.values[6] = 'ind'
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        mean = df.iloc[:, 6].rolling(window).mean()
        upper_bound = mean + df.iloc[:, 6].rolling(window).std() * upper_sig
        lower_bound = mean - df.iloc[:, 6].rolling(window).std() * lower_sig

        df.loc[df.loc[:, df.columns.values[6]] > upper_bound, f'short_signal'] = 1
        df.loc[df.loc[:, df.columns.values[6]] < lower_bound, f'long_signal'] = 1

        # exit signal
        idx = np.where((df['ind'] < upper_bound) & (df['ind'] > lower_bound))
        df.loc[idx[0], f'exit_signal'] = 1

        return df


class BollingerBandTF(Strategy):
    def __init__(self, ord_type: str, slippage: float, price_data: pd.DataFrame, param: dict, indicator: pd.DataFrame):
        super().__init__(ord_type, slippage, price_data, indicator, param)

    def generate_signal(self, df):
        '''
        param: window, upper_sig, lower_sig
        :return: dataframe with signals
        '''
        window = self.param['window']
        upper_sig = self.param['upper_sig']
        lower_sig = self.param['lower_sig']
        # change the name of indicator columns to sth general
        df.columns.values[6] = 'ind'
        df.replace([np.inf, -np.inf], np.nan, inplace=True)

        mean = df.iloc[:, 6].rolling(window).mean()
        upper_bound = mean + df.iloc[:, 6].rolling(window).std() * upper_sig
        lower_bound = mean - df.iloc[:, 6].rolling(window).std() * lower_sig

        df.loc[df.loc[:, df.columns.values[6]] > upper_bound, f'long_signal'] = 1
        df.loc[df.loc[:, df.columns.values[6]] < lower_bound, f'short_signal'] = 1

        # exit signal
        idx = np.where((df['ind'] < upper_bound) & (df['ind'] > lower_bound))
        df.loc[idx[0], f'exit_signal'] = 1
        df = df.set_index('date', drop=True)

        return df