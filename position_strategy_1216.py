#! /Users/liyuefan/anaconda2/bin/python
#  coding: utf-8


import copy
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import create_engine

# from HMM_Cal import adaboost_execute as execute
from HMM_Cal import execute

warnings.filterwarnings(action='ignore')


class gtja_commodity(object):
    def __init__(self, brokerName, engine, category, data_source):
        self.brokerName = brokerName
        self.engine = engine
        self.data_source = data_source
        self.category = category

    def load_data(self):
        if len(self.category) > 1:
            self.category_1 = self.category[0].upper() + self.category[1:].lower()
        elif len(self.category) == 1:
            self.category_1 = copy.deepcopy(self.category)
            self.category_1 = self.category.upper()
        else:
            raise Exception("parameter error!")

        print self.category_1

        for i in range(len(self.brokerName)):
            if len(self.brokerName) > 1:
                if i == 0:
                    self.brokerNameParenth = '(' + '\'' + self.brokerName[i].encode('utf8') + '\'' + ','
                elif i > 0 and i < len(self.brokerName) - 1:
                    self.brokerNameParenth += '\'' + self.brokerName[i].encode('utf8') + '\'' + ','
                else:
                    self.brokerNameParenth += '\'' + self.brokerName[i].encode('utf8') + '\'' + ')'
            else:
                self.brokerNameParenth = '(' + '\'' + self.brokerName[i].encode('utf8') + '\'' + ')'

        print "select distinct * from gtja_intern.%s_volume_data where company_name_2 in %s or company_name_3 in %s and contract='全部合约'" % (
        self.category, self.brokerNameParenth, self.brokerNameParenth)

        if self.data_source == 'dalian':
            position_data = pd.read_sql_query(
                "select distinct * from gtja_intern.%s_volume_data where company_name_2 in %s "
                "or company_name_3 in %s and contract='全部合约'" % (
                self.category, self.brokerNameParenth, self.brokerNameParenth), self.engine)
        elif self.data_source == 'shanghai':
            position_data = pd.read_sql_query(
                "select distinct * from gtja_intern.%s_volume_data where company_name_2 in %s "
                "or company_name_3 in %s and category='%s'" % (
                self.category, self.brokerNameParenth, self.brokerNameParenth, self.category), self.engine)
        position_data = position_data.iloc[:, 4:]
        position_data['update_date'] = pd.to_datetime(position_data['update_date'])
        if self.data_source == 'dalian':
            position_data['hold_vol_buy'] = position_data['hold_vol_buy'].apply(
                lambda x: float(x.replace(',', '')) if x != u'\xa0' else np.nan)
            position_data['hold_vol_buy_chg'] = position_data['hold_vol_buy_chg'].apply(
                lambda x: float(x.replace(',', '')) if x != u'\xa0' else np.nan)
            position_data['hold_vol_sell'] = position_data['hold_vol_sell'].apply(
                lambda x: float(x.replace(',', '')) if x != u'\xa0' else np.nan)
            position_data['hold_vol_sell_chg'] = position_data['hold_vol_sell_chg'].apply(
                lambda x: float(x.replace(',', '')) if x != u'\xa0' else np.nan)
            position_data['company_name_2'] = position_data['company_name_2'].apply(lambda x: x.replace(' ', ''))
            position_data['company_name_3'] = position_data['company_name_3'].apply(lambda x: x.replace(' ', ''))
        elif self.data_source == 'shanghai':
            position_data['hold_vol_buy'] = position_data['hold_vol_buy'].apply(
                lambda x: float(x) if x != u'\xa0' else np.nan)
            position_data['hold_vol_buy_chg'] = position_data['hold_vol_buy_chg'].apply(
                lambda x: float(x) if x != u'\xa0' else np.nan)
            position_data['hold_vol_sell'] = position_data['hold_vol_sell'].apply(
                lambda x: float(x) if x != u'\xa0' else np.nan)
            position_data['hold_vol_sell_chg'] = position_data['hold_vol_sell_chg'].apply(
                lambda x: float(x) if x != u'\xa0' else np.nan)
            position_data['company_name_2'] = position_data['company_name_2'].apply(lambda x: x.replace(' ', ''))
            position_data['company_name_3'] = position_data['company_name_3'].apply(lambda x: x.replace(' ', ''))
        index_data = pd.read_csv("%sFI_1209.csv" % self.category.upper(), header=0, encoding='gbk')
        index_data['update_date'] = pd.to_datetime(index_data['update_date'])
        index_data = index_data.sort('update_date')

        position_turn_over = index_data.loc[:, ['update_date', 'volume', 'position_all']]
        position_turn_over['update_date'] = pd.to_datetime(position_turn_over['update_date'])
        position_turn_over = position_turn_over.sort(['update_date'])
        position_turn_over['position_diff'] = position_turn_over['position_all'].diff()
        position_turn_over['turn_over_rate'] = position_turn_over['volume'] / position_turn_over['position_diff']

        def abs_(x):
            try:
                return np.abs(x)
            except:
                return np.nan

        position_turn_over['turn_over_rate'] = position_turn_over['turn_over_rate'].apply(abs_)

        return position_data, index_data, position_turn_over

    def organize_data(self):
        position_data, index_data, position_turn_over = self.load_data()

        ####index_data####
        ##calculate moving average to find the trend
        index_data['MA5'] = pd.rolling_mean(index_data['close'], 30)
        index_data['MA10'] = pd.rolling_mean(index_data['close'], 60)

        index_data['trend'] = index_data['MA5'] - index_data['MA10']

        index_data = index_data.sort(['update_date'])
        for col in ['trend', 'MA5', 'MA10', 'position_all']:
            index_data[col] = index_data[col].shift(1)
        index_data['log_open'] = np.log(index_data['open'])
        index_data['return_rate'] = index_data['log_open'].diff()
        index_data = index_data.drop(['log_open'], axis=1)

        def hmm(category):
            def hmm_with_category(day):
                return execute(day, category)

            return hmm_with_category

        exe = hmm(self.category.upper())

        # index_data['trend']=map(exe,index_data['update_date'])

        ####position_data####
        def position_org(position_data):
            self.position_data_org = pd.DataFrame(
                columns=['company_name', 'position', 'position_chg', 'update_date', 'contract'])
            temp = position_data[['company_name_2', 'hold_vol_buy', 'hold_vol_buy_chg', 'update_date', 'contract']]
            temp = temp.rename(columns={'company_name_2': 'company_name', 'hold_vol_buy': 'position',
                                        'hold_vol_buy_chg': 'position_chg'})
            temp['direction_tag'] = temp['position_chg'].apply(lambda x: 10 if x > 0 else 0)
            temp['tag'] = 'pos'
            self.position_data_org = self.position_data_org.append(temp)
            temp = position_data[['company_name_3', 'hold_vol_sell', 'hold_vol_sell_chg', 'update_date', 'contract']]
            temp = temp.rename(columns={'company_name_3': 'company_name', 'hold_vol_sell': 'position',
                                        'hold_vol_sell_chg': 'position_chg'})
            temp['position'] = -1 * temp['position']
            temp['position_chg'] = -1 * temp['position_chg']
            temp['direction_tag'] = temp['position_chg'].apply(lambda x: 1 if x < 0 else 0)
            temp['tag'] = 'neg'
            self.position_data_org = self.position_data_org.append(temp)
            return self.position_data_org

        self.position_data_org = position_org(position_data)

        self.position_data_org_2 = self.position_data_org.groupby(['update_date', 'company_name']).sum()
        try:
            self.position_data_org_2 = self.position_data_org_2.drop(['contract'], axis=1)
            self.position_data_org_1 = self.position_data_org.groupby(['update_date', 'company_name']).contract.count()
            self.position_data_org = pd.concat([self.position_data_org_2, self.position_data_org_1], axis=1,
                                               join='inner')
            self.position_data_org = self.position_data_org.loc[:,
                                     ['position', 'position_chg', 'direction_tag', 'contract']]
        except:
            self.position_data_org = self.position_data_org_2
            self.position_data_org['contract'] = 1
        self.position_data_org.reset_index(inplace=True)

        # 取出特定交易商的交易持仓变化记录
        self.position_data_selected = pd.DataFrame(columns=self.position_data_org.columns)
        for item in self.brokerName:
            print item
            temp = self.position_data_org[self.position_data_org['company_name'] == item]
            if len(temp) != 0:
                self.position_data_selected = self.position_data_selected.append(temp)
            else:
                print 'cannot find %s in data, please check...' % item

        # 将全量日期对上筛选后的数据
        self.position_data_selected = pd.merge(index_data[['update_date']], self.position_data_selected,
                                               on=['update_date'], how='outer')
        ##将今天收盘得到的数据设定为明天的决策依据
        self.position_data_lagged = pd.DataFrame()
        for i, j in self.position_data_selected.groupby('company_name'):
            j = j.sort('update_date')
            for col in ['position', 'position_chg', 'direction_tag']:
                j[col] = j[col].shift(1)

                self.position_data_lagged = self.position_data_lagged.append(j)

        ####position_turn_over####
        position_turn_over = position_turn_over.loc[:, ['update_date', 'turn_over_rate']]
        position_turn_over['turn_over_rate'] = position_turn_over['turn_over_rate'].shift(1)
        return index_data, self.position_data_lagged, position_turn_over

    def position_rule(self, quantile_high, quantile_low):
        index_data, position_data, turn_over = self.organize_data()
        self.index_data = index_data
        position_data = pd.merge(position_data, index_data[['update_date', 'position_all']], on=['update_date'],
                                 how='outer')
        position_data['position_chg'] = position_data['position_chg'] / position_data['position_all']

        t = pd.DataFrame()
        for i, j in position_data.groupby(['company_name']):
            j = j.sort(['update_date'])
            j['position_chg_high'] = j['position_chg'].rolling(250).quantile(quantile_high)
            j['position_chg_low'] = j['position_chg'].rolling(250).quantile(quantile_low)
            t = t.append(j)

        position_data = t
        position_data['temp_high'] = position_data['position_chg'] - position_data['position_chg_high']
        position_data['temp_low'] = position_data['position_chg'] - position_data['position_chg_low']

        position_data['temp_high'] = position_data['temp_high'].apply(lambda x: 1 if x > 0 else np.nan)
        position_data['temp_low'] = position_data['temp_low'].apply(lambda x: -1 if x < 0 else np.nan)
        position_data['position_signal'] = position_data['temp_high']
        position_data['position_signal'] = position_data['position_signal'].fillna(position_data['temp_low'])

        def dir_tag(x):
            if np.isnan(x) == False:
                x = int(x)
                if x / 10 > 0 and x % 10 == 0:
                    return 1
                elif x / 10 == 0 and x % 10 > 0:
                    return -1
            else:
                return np.nan

        position_data['temp_dir'] = position_data['direction_tag'].apply(dir_tag)
        position_data['position_signal'] = (position_data['temp_dir'] + position_data['position_signal']) / 2.

        def g(x):
            if x == 1:
                return 1
            elif x == -1:
                return -1
            else:
                return np.nan

        position_data['position_signal'] = position_data['position_signal'].apply(g)
        position_data = position_data.drop(['temp_high', 'temp_low', 'temp_dir'], axis=1)
        return position_data

    def index_data_rule(self):
        index_data = self.index_data

        def trend_dir(x):
            if x > 0:
                return 1
            elif x < 0:
                return -1
            else:
                return np.nan

        index_data['index_signal'] = index_data['trend'].apply(trend_dir)
        return index_data

    def start_signal(self):
        p = self.position_rule(0.95, 0.05)
        i = self.index_data_rule()
        df = pd.merge(p[['company_name', 'update_date', 'position_signal']], i, on=['update_date'], how='outer')
        # index_signal表示趋势信号,position_signal表示仓位变化信号

        df['index_position_signal'] = df['position_signal'] + df['index_signal']
        df['index_position_signal'] = df['index_position_signal'] / 2.

        def g(x):
            if x == 1:
                return 1
            elif x == -1:
                return -1
            else:
                return np.nan

        df['index_position_signal'] = df['index_position_signal'].apply(g)
        df = df.sort(['update_date'])
        df['index_position_signal'] = df['index_position_signal'].fillna(method='ffill')
        return df

    def stop_loss(self, trailing_threshold, hard_threshold):
        df = self.start_signal()
        df['trade_num'] = np.nan
        count = 1
        t = pd.DataFrame()
        for i, j in df.groupby(['company_name']):
            j = j.sort(['update_date'])

            j['index_position_signal'] = j['index_position_signal'].fillna(0)
            j['index_position_signal'] = j['index_position_signal'].diff()
            j['index_position_signal'] = j['index_position_signal'].fillna(0)

            def f(x):
                if x > 0:
                    return 1
                elif x < 0:
                    return -1
                else:
                    return 0

            j['index_position_signal'] = j['index_position_signal'].apply(f)
            j['index_position_signal'] = j['index_position_signal'].fillna(0)
            j['trade_num'] = j['index_position_signal'].apply(abs)
            j['trade_num'] = j['trade_num'].cumsum()
            j['trade_num'] = j['trade_num'].apply(lambda x: int(str(count) + str(x)))
            j['index_position_signal'] = j['index_position_signal'].apply(lambda x: np.nan if x == 0 else x)
            j['index_position_signal'] = j['index_position_signal'].fillna(method='ffill')
            j['index_position_signal'] = j['index_position_signal'].fillna(0)
            count += 1
            t = t.append(j)

        df = t
        df['daily_return'] = df['return_rate'] * df['index_position_signal']
        print len(pd.unique(df['trade_num']))

        def threshold(x):
            if x <= 0.02:
                return hard_threshold
            elif x > 0.02:
                return trailing_threshold * x
            else:
                pass

        t = pd.DataFrame()
        for i, j in df.groupby(['trade_num']):
            j = j.sort(['update_date'])
            j['cum_return'] = j['daily_return'].cumsum()
            j.iloc[0, :]['daily_return'] = j.iloc[0, :]['daily_return'] - 10.0 / 10000
            j['max_return'] = j['cum_return'].cummax()
            j['stoploss_point'] = j['max_return'].apply(threshold)
            j['stoploss_point'] = j['stoploss_point'].shift(1)
            j['stoploss_or_not'] = j['cum_return'] - j['stoploss_point']
            temp = j[j['stoploss_or_not'] < 0]
            temp = temp.sort(['update_date'])
            if len(temp) > 0:
                cum_return = 1 + temp.iloc[0, :]['stoploss_point']
            else:
                cum_return = 1 + j.iloc[-1, :]['cum_return']
            j['stoploss_or_not'] = j['stoploss_or_not'].apply(
                lambda x: 0 if x > 0 else x + 10. * cum_return / 10000)  ##此处为交易成本和滑点的近似
            j['daily_return'] = j['daily_return'] - j['stoploss_or_not']
            j['stoploss_or_not'] = j['stoploss_or_not'].apply(lambda x: 0 if x < 0 else 1)
            j['stoploss_or_not'] = j['stoploss_or_not'].shift(1)
            j['stoploss_or_not'] = j['stoploss_or_not'].fillna(method='bfill')
            t = t.append(j)
        df = t
        df['daily_return'] = df['daily_return'] * df['stoploss_or_not']
        df['index_position_signal'] = df['index_position_signal'] * df['stoploss_or_not']
        df = df.sort(['update_date'])
        return df


if __name__ == '__main__':
    engine = create_engine("mysql+pymysql://liyuefan:1994050306@localhost/gtja_intern?charset=utf8")
    asset_1 = gtja_commodity([u'新湖期货', u'永安期货', u'浙商期货'], engine, 'zn', 'shanghai')
    raw = asset_1.stop_loss(0.75, -0.02)
    raw = raw.loc[:, ['company_name', 'update_date', 'index_position_signal', 'daily_return']]
    x = 1
    for i, j in raw.groupby(['company_name']):
        j = j.sort(['update_date'])
        j['daily_return'] = j['daily_return'] / j['index_position_signal'].apply(lambda x: abs(float(x)))
        j['daily_return'] = j['daily_return'].fillna(0)
        j['cum_return'] = j['daily_return'].cumsum()
        j['max_return'] = j['cum_return'].cummax()
        j['drawdown'] = j['max_return'] - j['cum_return']
        j.index = [j['update_date']]
        sharpe = (np.mean(j['daily_return']) * 252 - 0.03) / (np.std(j['daily_return']) * np.sqrt(252))
        plt.subplot(3, 1, x)
        plt.plot(j['update_date'], j['cum_return'], label='%s: %s' % (i, sharpe))
        plt.bar(j.index, j['index_position_signal'])
        plt.legend(loc='upper left')
        x += 1
    plt.show()
