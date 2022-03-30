import pandas as pd

from Exchange import ExchangeRule
from Strategy import Strategy
import numpy as np

class BTengine:
    def __init__(self, initial_capital: float, exchange: ExchangeRule, strat: Strategy):
        self.init_capital = initial_capital
        self.exchange = exchange
        self.strategy = strat

    def exchange_info(self):
        info = {'maker': self.exchange.makerFee,
                'taker': self.exchange.takerFee,
                'min_order_val': self.exchange.min_val}
        return info

    def prep_data(self):
        raw_df = self.strategy.data.copy()
        ind = self.strategy.indicator.copy()
        raw_df = raw_df.set_index('date').join(ind.set_index('date'))
        raw_df = raw_df.reset_index()

        return raw_df

    def run(self, input_df: pd.DataFrame):
        df = self.strategy.generate_signal(input_df)
        if self.strategy.order_t == 'MARKET':
            isLong = False
            isShort = False
            entryp = 0
            df.loc[0, 'capital'] = self.init_capital
            for i in range(len(df)):
                if i == 0:
                    continue

                # entry
                elif (isLong is False) and (isShort is False) and df.loc[i - 1, f'long_signal'] == 1:
                    entryp = df.loc[i, 'open']
                    df.loc[i, 'pnl'] = 1 - (self.exchange.takerFee + self.strategy.slippage)
                    df.loc[i, 'capital'] = df.loc[i - 1, 'capital'] * df.loc[i, 'pnl']
                    isLong = True
                elif (isLong is False) and (isShort is False) and df.loc[i - 1, f'short_signal'] == 1:
                    entryp = df.loc[i, 'open']
                    df.loc[i, 'pnl'] = 1 - (self.exchange.takerFee + self.strategy.slippage)
                    df.loc[i, 'capital'] = df.loc[i - 1, 'capital'] * df.loc[i, 'pnl']
                    isShort = True

                # exit
                elif isLong is True and df.loc[i - 1, f'exit_signal'] == 1:
                    exitp = df.loc[i, 'open']
                    df.loc[i, 'pnl'] = exitp / entryp
                    df.loc[i, 'capital'] = df.loc[i, 'pnl'] * df.loc[i - 1, 'capital']
                    isLong = False
                elif isShort is True and df.loc[i - 1, f'exit_signal'] == 1:
                    exitp = df.loc[i, 'open']
                    df.loc[i, 'pnl'] = 2 - exitp / entryp  # (entry - exit)/entry + 1 = 1 - exit
                    df.loc[i, 'capital'] = df.loc[i, 'pnl'] * df.loc[i - 1, 'capital']
                    isShort = False

                else:
                    df.loc[i, 'capital'] = df.loc[i - 1, 'capital']

        if df.loc[len(df) - 1, 'capital'] < 0:
            CAGR = 0
            MDD = -1
            SR = 0
            df.loc[df['capital'] < 0] = 0
        else:
            CAGR = (df.loc[len(df) - 1, 'capital'] / df.loc[0, 'capital']) ** (365 / len(df)) - 1

            roll_max_cap = df['capital'].max()
            daily_drawdown = (df['capital'] / roll_max_cap) - 1.0
            MDD = daily_drawdown.min()

            if 'pnl' not in df.columns:
                SR = 0
            else:
                expectedReturn = (df['pnl'] - 1).mean()
                stdReturn = (df['pnl'] - 1).std()
                SR = (expectedReturn / stdReturn) * (365 ** (1 / 2))

        final_result = {'CAGR': CAGR, 'final balance': df.loc[len(df) - 1, 'capital'], 'MDD': MDD, 'SR': SR}

        return df, final_result

    def optimize(self, num_tries: int, target: str, space: dict, input_df: pd.DataFrame):
        param = self.strategy.param
        param_name = list(param.keys())
        best_param = param
        df, past_result = self.run(input_df)

        # iteration
        for i in range(num_tries):
            past_param = self.strategy.param.copy()
            for j in range(len(param_name)):
                randNum = np.random.uniform(high=space[param_name[j]][1], low=space[param_name[j]][0])
                if space[param_name[j]][2] == 'int':
                    randNum = int(randNum)
                self.strategy.update_param(param_name[j], randNum)

            # generate result based on new param
            new_param = self.strategy.param.copy()
            df, new_result = self.run(input_df)

            if float(past_result[target]) >= float(new_result[target]):  # if past is better than new, keep past param
                self.strategy.param = past_param

            else:  # else keep the param into a variable.
                if new_result[target] == np.nan:
                    continue
                past_result = new_result
                self.strategy.param = new_param
                best_param = self.strategy.param

        df, final_res = self.run(input_df)
        return best_param, final_res

    def test(self, num_tries: int, target: str, space: dict, k: int):
        raw_df = self.prep_data()

        validation_sets = [raw_df.loc[i-int(len(raw_df) / k):i].reset_index(drop=True) for i in
                           range(int(len(raw_df) / k), len(raw_df), int(len(raw_df) / k))]

        history = []
        trading_days = 0
        for i in range(k):
            temp = validation_sets.copy()
            train = temp[i].loc[:int(len(temp[i]) * 0.8)]
            val_test = temp[i].loc[int(len(temp[i]) * 0.8):].reset_index(drop=True)
            param, res = self.optimize(num_tries, target, space, train)  # optimize param using 4/5 train samples
            self.strategy.param = param  # set the parameter to optimized value
            df, final_res = self.run(pd.DataFrame(val_test))  # test using the remaining 1/5 train sample
            trading_days += len(val_test)
            history.append(final_res)

        # CAGR
        init_bal = self.init_capital * k
        ending_bal = 0
        for i in range(len(history)):
            ending_bal += history[i]['final balance']
        CAGR = (ending_bal/init_bal)**(365/trading_days) - 1

        final_bal = 0
        MDD = 0
        SR = 0
        for i in range(len(history)):
            final_bal += history[i]['final balance']
            MDD += history[i]['MDD']
            SR += history[i]['SR']

        report = {'CAGR': CAGR, 'final balance': final_bal, 'avg_MDD': MDD/len(history),
                  'avg_SR': SR/len(history), 'trading days': trading_days, 'k': k}
        return report
