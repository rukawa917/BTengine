from Exchange import ExchangeRule
from Engine import BTengine
import Strategy

import pandas as pd
import os

import sys

# if not sys.warnoptions:
#     import warnings
#     warnings.simplefilter("ignore")


flist = sorted(os.listdir('/Users/chriskang/Library/CloudStorage/OneDrive-HKUSTConnect/Pycharm/COMP4971/onchain_strategy/Data/day'))
data = pd.read_parquet('/Users/chriskang/Library/CloudStorage/OneDrive-HKUSTConnect/Pycharm/COMP4971/onchain_strategy/Data/day/ohlcv_Binance_day.parquet.gzip')

# strategy Allocation
BBMR = ['btc_reserve_all_exchange_day.parquet.gzip', 'btc_inflow_all_exchange_day.parquet.gzip',
        'stablecoinR_all_exchange_day.parquet.gzip']
# BBTF =

for file in flist:
    print(file)
    if file == 'ohlcv_Binance_day.parquet.gzip' or file == 'ohlcv_all_exchange_day.parquet.gzip':
        continue
    ind = pd.read_parquet(f'/Users/chriskang/Library/CloudStorage/OneDrive-HKUSTConnect/Pycharm/COMP4971/onchain_strategy/Data/day/{file}')
    col = ind.columns.values
    for i in range(len(col)):
        if i == 0:
            continue
        temp_ind = ind[[col[0], col[i]]]

        print(col[i])
        Ex = ExchangeRule(maker=0.01, taker=0.005, min_val=10)
        param = {'window': 100, 'upper_sig': 1.5, 'lower_sig': 1.5}
        if file in BBMR:
            strategy = Strategy.BollingerBandMR(ord_type='MARKET', slippage=0.002, price_data=data, indicator=temp_ind,
                                     param=param)
        else:
            continue
        obj = BTengine(initial_capital=10000, exchange=Ex, strat=strategy)
        space = {'window': (10, 30, 'int'), 'upper_sig': (1, 2.5, 'float'), 'lower_sig': (1, 2.5, 'float')}
        test_result = obj.test(num_tries=400, target='CAGR', space=space, k=4)
        #df.to_csv(f'test{col[i]}.csv')
        print(test_result)
