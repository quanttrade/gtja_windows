#! /Users/liyuefan/anaconda2/bin/python
#  coding: utf-8


import copy
import datetime
import time
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import wrapt
from sqlalchemy import create_engine

# from HMM_Cal import adaboost_execute as execute
from HMM_Cal import execute

warnings.filterwarnings(action='ignore')


@wrapt.decorator
def timeit(func, instance, args, kwargs):
    t = time.time()
    ans = func(*args, **kwargs)
    t = time.time() - t
    print func.__name__, t
    return ans


class gtja_commodity(object):
    # 初始化参数，包括跟踪的期货商的名称（list），数据库连接，期货品种，数据来源（大连或上海）
    def __init__(self, brokerName, engine, category, data_source):
        self.brokerName = brokerName
        self.engine = engine
        self.data_source = data_source
        self.category = category

    # 加载数据
    @timeit
    def load_data(self):
        # 将品种字段改成符合数据文件命名规则的大小写，方便之后从csv和数据库中提取数据
        if len(self.category) > 1:
            self.category_1 = self.category[0].upper() + self.category[1:].lower()
        elif len(self.category) == 1:
            self.category_1 = copy.deepcopy(self.category)
            self.category_1 = self.category.upper()
        else:
            raise Exception("parameter error!")

        print self.category_1

        # 将期货商list重新改写成符合sql查询语句语法的字符串
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

        # 从sql数据库提取数据
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
        # 只取空头和多头仓位，不取前四列（总仓位）
        position_data = position_data.iloc[:, 4:]
        position_data['update_date'] = pd.to_datetime(position_data['update_date'])
        # 将从sql中提取的数据中的空格去掉（sql中网页抓取的数字都是按照字符串型进行存储的，此处需要转换为浮点型）
        if self.data_source == 'dalian':
            # 去空格
            position_data['hold_vol_buy'] = position_data['hold_vol_buy'].apply(
                lambda x: float(x.replace(',', '')) if x != u'\xa0' else np.nan)
            # 去千分位符
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

        # 读取活跃合约连续数据（也可换为wind商品指数）
        index_data = pd.read_csv("%sFI_1209.csv" % self.category.upper(), header=0, encoding='gbk')
        index_data['update_date'] = pd.to_datetime(index_data['update_date'])
        index_data = index_data.sort('update_date')

        # 计算换手数据（原本作为平仓条件使用，但是目前不使用该条件平仓）
        position_turn_over = index_data.loc[:, ['update_date', 'volume', 'position_all']]
        position_turn_over['update_date'] = pd.to_datetime(position_turn_over['update_date'])
        position_turn_over = position_turn_over.sort(['update_date'])
        position_turn_over['position_diff'] = position_turn_over['position_all'].diff()
        position_turn_over['turn_over_rate'] = position_turn_over['volume'] / position_turn_over['position_diff']

        # 换手率直接用绝对值进行比较，所以定义该函数。由于原始数据中存在空值和inf等异常值，所以需要进行一个逻辑判断
        def abs_(x):
            try:
                return np.abs(x)
            except:
                return np.nan

        position_turn_over['turn_over_rate'] = position_turn_over['turn_over_rate'].apply(abs_)

        return position_data, index_data, position_turn_over

    @timeit
    def organize_data(self):
        position_data, index_data, position_turn_over = self.load_data()

        ####index_data####
        ##calculate moving average to find the trend
        index_data['MA5'] = pd.rolling_mean(index_data['close'], 30)
        index_data['MA10'] = pd.rolling_mean(index_data['close'], 60)

        # 取差值作为趋势的等价
        index_data['trend'] = index_data['MA5'] - index_data['MA10']

        # 由于开仓信号取决于仓位信号和趋势信号，所以为了避免未来函数，需要对这些开仓信号变量进行移动。
        # 由于定为收盘时进行开仓和平仓操作，例子：2016/8/1日收盘后得到的趋势和仓位信号的原始日期标签是2016/8/1，
        # 但是要等到2016/8/2收盘时才会运用到8/1收盘后的数据进行仓位的操作，所以8/1日的信号决定的收益是从2016/8/2日收盘
        # 到2016/8/3日收盘之间的收益，在原始数据中，这个收益的日期标签是2016/8/3，所以需要对原始决策数据向后移动两天，
        # 以在计算收益时能够对其对应的当日收益
        index_data = index_data.sort(['update_date'])
        for col in ['trend', 'MA5', 'MA10', 'position_all']:
            index_data[col] = index_data[col].shift(2)  # 原来是错位1
        # 按照收盘价计算日对数收益率
        index_data['log_open'] = np.log(index_data['close'])
        index_data['return_rate'] = index_data['log_open'].diff()
        index_data = index_data.drop(['log_open'], axis=1)

        # 为hmm模块预留的闭包函数，并未使用
        def hmm(category):
            def hmm_with_category(day):
                return execute(day, category)

            return hmm_with_category

        exe = hmm(self.category.upper())

        # 为hmm模块预留的闭包函数，并未使用
        #         index_data['trend']=map(exe,index_data['update_date'])
        #         index_data['trend']=index_data['trend'].shift(1)

        ####position_data####
        # 将原始数据中横向排列的多头和空头仓位数据重新纵向排列，对空头的仓位都乘以-1（空桶增仓的符号为-）
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
        # 计算每日活跃合约总数
        try:
            self.position_data_org_2 = self.position_data_org_2.drop(['contract'], axis=1)
            self.position_data_org_1 = self.position_data_org.groupby(['update_date', 'company_name']).contract.count()
            self.position_data_org = pd.concat([self.position_data_org_2, self.position_data_org_1], axis=1,
                                               join='inner')
            self.position_data_org = self.position_data_org.loc[:,
                                     ['position', 'position_chg', 'direction_tag', 'contract']]
        # 如果失败则令每日的活跃合约总数为1
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

        # 将全量日期对上筛选后的数据（因为无法保证特定交易商每天都出现在前二十大持仓中）
        self.position_data_selected = pd.merge(index_data[['update_date']], self.position_data_selected,
                                               on=['update_date'], how='left')
        ##将今天收盘得到的数据设定为后天的决策依据
        # 理由同index_data中的错位
        self.position_data_lagged = pd.DataFrame()
        for i, j in self.position_data_selected.groupby('company_name'):
            j = j.sort('update_date')
            for col in ['position', 'position_chg', 'direction_tag']:
                j[col] = j[col].shift(2)  ##原来为1
            self.position_data_lagged = self.position_data_lagged.append(j)

        ####position_turn_over####
        # 也要对换手率进行错位（若假定收盘才平仓）
        position_turn_over = position_turn_over.loc[:, ['update_date', 'turn_over_rate']]
        position_turn_over['turn_over_rate'] = position_turn_over['turn_over_rate'].shift(2)  ##原来为1
        return index_data, self.position_data_lagged, position_turn_over

    @timeit
    def position_rule(self, quantile_high, quantile_low):
        index_data, position_data, turn_over = self.organize_data()
        # index_data在index_rule中也会用到，所以将其作为对象的一个属性，方便之后直接使用，而不用重复计算
        self.index_data = index_data
        # 将每天的总持仓量数据对上每家期货公司每天的持仓变化信息
        position_data = pd.merge(position_data, index_data[['update_date', 'position_all']], on=['update_date'],
                                 how='left')
        # 将持仓变化除以总持仓，得到标准化之后的每日持仓变化
        position_data['position_chg'] = position_data['position_chg'] / position_data['position_all']
        position_data['position_chg'] = position_data['position_chg'].fillna(0)

        t = pd.DataFrame()
        # 滚动求每家的持仓量变化分位点阈值
        for i, j in position_data.groupby(['company_name']):
            j = j.sort(['update_date'])
            j['position_chg_high'] = j['position_chg'].rolling(250).quantile(quantile_high)
            j['position_chg_low'] = j['position_chg'].rolling(250).quantile(quantile_low)
            t = t.append(j)

        position_data = t

        # 计算高于阈值和低于阈值的记录
        position_data['temp_high'] = position_data['position_chg'] - position_data['position_chg_high']
        position_data['temp_low'] = position_data['position_chg'] - position_data['position_chg_low']

        position_data['temp_high'] = position_data['temp_high'].apply(lambda x: 1 if x > 0 else np.nan)
        position_data['temp_low'] = position_data['temp_low'].apply(lambda x: -1 if x < 0 else np.nan)
        position_data['position_signal'] = position_data['temp_high']
        position_data['position_signal'] = position_data['position_signal'].fillna(position_data['temp_low'])

        # 计算持仓量变化的细节方向：
        # 当总持仓变化增加极大时，同时需要满足以下条件：多头增加且空头未减少（即净仓位增加不是由空头减少、而是由多头增加带来的）
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
        # 如果净仓位变化大但是仓位方向不对，则仓位信号不为1或者-1
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

    @timeit
    def index_data_rule(self):
        index_data = self.index_data

        def trend_dir(x):
            if x > 0:
                return 1
            elif x < 0:
                return -1
            else:
                return np.nan

        # 确定趋势信号方向
        index_data['index_signal'] = index_data['trend'].apply(trend_dir)
        return index_data

    @timeit
    def start_signal(self):
        # 取0.9分位点作为仓位变化上分位点，0.1作为下分位点，取这两个分位点两侧的数据作为“仓位显著变化”
        p = self.position_rule(0.7, 0.3)

        i = self.index_data_rule()
        df = pd.merge(p[['company_name', 'update_date', 'position_signal']], i, on=['update_date'], how='left')

        # index_signal表示趋势信号,position_signal表示仓位变化信号

        # 趋势信号和仓位信号需要同时为一个方向才发出开仓信号
        df['index_position_signal'] = df['position_signal'] + df['index_signal']
        df['index_position_signal'] = df['index_position_signal'] / 2.

        def g(x):
            if x == 1:
                return 1
            elif x == -1:
                return -1

            else:
                #                 return np.nan
                return np.nan

        df['index_position_signal'] = df['index_position_signal'].apply(g)
        df = df.sort(['update_date'])
        # 向后填充仓位信号空值
        #         df['index_position_signal']=df['index_position_signal'].fillna(method='ffill')
        return df

    @timeit
    def stop_loss(self, trailing_threshold, hard_threshold):
        df = self.start_signal()
        # 给不同的单笔交易贴上标签，方便之后计算单笔交易的止损
        df['trade_num'] = np.nan
        count = 1
        t = pd.DataFrame()
        for i, j in df.groupby(['company_name']):
            j = j.sort(['update_date'])

            j['index_position_signal_2'] = j['index_position_signal'].fillna(method='ffill')
            j['index_position_singal_2'] = j['index_position_signal_2'].fillna(0)
            j['index_position_signal_2'] = j['index_position_signal_2'].diff()

            #             j['index_position_signal']=j['index_position_signal'].fillna(0)
            def f(x):
                if x > 0:
                    return 1
                elif x < 0:
                    return -1
                else:
                    return 0

            j['index_position_signal_2'] = j['index_position_signal_2'].apply(f)
            #             j['index_position_signal_2']=j['index_position_signal_2'].fillna(0)
            j['trade_num'] = j['index_position_signal_2'].apply(abs)
            j['trade_num'] = j['trade_num'].cumsum()
            j['trade_num'] = j['trade_num'].apply(lambda x: int(str(count) + str(int(x))))
            j = j.drop(['index_position_signal_2'], axis=1)
            #             j['index_position_signal']=j['index_position_signal'].apply(lambda x: np.nan if x==0 else x)
            j['index_position_signal'] = j['index_position_signal'].fillna(method='ffill')
            j['index_position_signal'] = j['index_position_signal'].fillna(0)
            count += 1
            t = t.append(j)

        df = t

        df['daily_return'] = df['return_rate'] * df['index_position_signal']

        def threshold(x):
            if x <= 0.02:
                return hard_threshold
            elif x > 0.02:
                return trailing_threshold * x
            else:
                pass

        t = pd.DataFrame()
        total_trade = []
        for i, j in df.groupby(['trade_num']):
            j = j.sort(['update_date'])
            j = j.drop_duplicates()
            j['cum_return'] = j['daily_return'].cumsum()
            #             j.iloc[0,:]['daily_return']=j.iloc[0,:]['daily_return']-10.0/10000#此处为交易成本和滑点近似
            j['max_return'] = j['cum_return'].cummax()
            j['stoploss_point'] = j['max_return'].apply(threshold)
            j['stoploss_point'] = j['stoploss_point'].shift(1)
            j['stoploss_or_not'] = j['cum_return'] - j['stoploss_point']
            if j.iloc[0, :]['index_position_signal'] > 0:
                j['stoploss_or_not'] = j['stoploss_or_not'] - ((j['close'] - j['low']) / j['close'])
            elif j.iloc[0, :]['index_position_signal'] < 0:
                j['stoploss_or_not'] = j['stoploss_or_not'] - ((j['high'] - j['close']) / j['close'])
            else:
                pass
            temp = j[j['stoploss_or_not'] < 0]
            temp = temp.sort(['update_date'])
            if len(temp) > 0:
                cum_return = 1 + temp.iloc[0, :]['stoploss_point']
            else:
                cum_return = 1 + j.iloc[-1, :]['cum_return']
            j['stoploss_or_not_return'] = j['stoploss_or_not'].apply(lambda x: 0 if x > 0 else x)  ##此处为交易成本和滑点的近似
            j['daily_return'] = j['daily_return'] - j['stoploss_or_not_return']  ##原来是-
            j['stoploss_or_not'] = j['stoploss_or_not'].apply(lambda x: 0 if x <= 0 else 1)  # 1 or np.nan?当为1时收益较高
            j['stoploss_or_not'] = j['stoploss_or_not'].fillna(method='ffill')
            j['stoploss_or_not'] = j['stoploss_or_not'].shift(1)
            j['stoploss_or_not'] = j['stoploss_or_not'].fillna(1)

            s = j[j['stoploss_or_not'] != 0]

            s['cum_return'] = s['daily_return'].cumsum()
            s['max_return'] = s['cum_return'].cummax()
            s['drawdown'] = s['cum_return'] - s['max_return']
            max_drawdown = np.min(s['drawdown'])
            w = s['cum_return'][-1:]
            w = w.values[0]
            l = len(s)
            broker = pd.unique(j['company_name'])
            start_date = np.min(j['update_date'])
            trade_record = [start_date, broker, w, max_drawdown, l]
            total_trade.append(trade_record)
            if w > 0:
                j['win_or_lose'] = 1. / len(j)
            else:
                j['win_or_lose'] = 0
            t = t.append(j)
        df = t
        #         df['daily_return']=df['daily_return']*df['stoploss_or_not']
        df['index_position_signal'] = df['index_position_signal'] * df['stoploss_or_not']
        df['daily_return'] = df['daily_return'] * df['index_position_signal'].apply(np.abs)
        df = df.sort(['update_date'])
        total_trade = pd.DataFrame(total_trade,
                                   columns=['update_date', 'company_name', 'cum_return', 'max_drawdown', 'length'])
        return df, total_trade


if __name__ == '__main__':
    st = datetime.datetime.now()
    p = {'category': 'zn', 'ex': 'shanghai'}
    engine = create_engine("mysql+pymysql://liyuefan:1994050306@localhost/gtja_intern?charset=utf8")
    asset_1 = gtja_commodity([u'新湖期货', u'永安期货', u'浙商期货'], engine, p['category'], p['ex'])
    pinyin = {u'新湖期货': 'xinhu', u'永安期货': 'yongan', u'浙商期货': 'zheshang', u'南华期货': 'nanhua', u'国泰君安': 'guojun',
              u'海通期货': 'haitong'}
    raw, total_trade = asset_1.stop_loss(0.75, -0.02)
    raw = raw.loc[:,
          ['company_name', 'update_date', 'index_position_signal', 'daily_return', 'win_or_lose', 'trade_num']]
    #     raw=raw[raw['update_date']>=pd.to_datetime('2016-05-01')]
    #     raw=raw[raw['update_date']<=pd.to_datetime('2016-06-01')]
    x = 1
    plt.figure(figsize=(15, 15))
    #     for i,j in raw.groupby(['company_name']):

    #         cor_rate=j['win_or_lose'].sum()/float(len(pd.unique(j['trade_num'])))
    #         j=j.sort(['update_date'])

    #         j=j.drop_duplicates()
    # #         j['daily_return']=j['daily_return']/j['index_position_signal'].apply(lambda x:abs(float(x)))

    #         col_list=list(j.columns)
    #         n=col_list.index('daily_return')
    #         for k in range(1,len(j)):
    #             if j.iloc[k-1,:]['index_position_signal']!=j.iloc[k,:]['index_position_signal'] and j.iloc[k,:]['index_position_signal']!=0:
    #                 j.iloc[k,n]=j.iloc[k,n]-20./10000
    #             else:
    #                 pass

    #         j['daily_return']=j['daily_return'].fillna(0)
    #         j['cum_return']=j['daily_return'].cumsum()
    #         j['max_return']=j['cum_return'].cummax()
    #         j['drawdown']=j['max_return']-j['cum_return']
    #         j.index=[j['update_date']]
    #         open_data=asset_1.index_data
    #         open_data=open_data[open_data['update_date']>=np.min(j['update_date'])]
    #         open_data=open_data[open_data['update_date']<=np.max(j['update_date'])]
    #         sharpe=(np.mean(j['daily_return'])*252-0.03)/(np.std(j['daily_return'])*np.sqrt(252))
    #         f1=plt.subplot(len(pinyin.items()),1,x)
    #         f2=f1.twinx()
    #         f1.plot(j['update_date'],j['cum_return'],'b.-',label='%s: %s'%(pinyin[i],sharpe))
    #         f2.plot(open_data['update_date'],open_data['close'],'r.-')
    #         f1.bar(j.index,j['index_position_signal'],alpha=0.6)
    #         f1.set_ylabel('cummulative_return')
    #         f2.set_ylabel('open price')
    #         f1.legend(loc='upper left')
    #         x+=1

    #         log='%s, broker: %s, cum_return: %s, SR: %s, ann_return: %s, volatility: %s, drawdown: %s, corr_rate: %s\n'%(p['category'] ,i.encode('utf-8'), j['cum_return'][-1],sharpe,np.mean(j['daily_return'])*252, np.std(j['daily_return'])*np.sqrt(252), np.max(j['drawdown']),cor_rate)
    # #         f=open('log_0.7_0.3.txt','a')
    # #         f.write(log)
    # #         f.close()
    #         print i, j['cum_return'][-1],sharpe,np.mean(j['daily_return'])*252, np.std(j['daily_return'])*np.sqrt(252), np.max(j['drawdown']),cor_rate

    #         j=j[j['update_date']>=pd.to_datetime('2016-10-01')]
    #         j=j[j['index_position_signal']>0]
    #         print np.min(j['update_date'])

    #     plt.savefig('%s_result.jpg'%p['category'])
    #     total_trade.to_csv('%s_total_record.csv'%p['category'],index=False,encoding='gbk')

    raw_return = pd.DataFrame()
    raw_return['daily_return'] = raw.groupby(['update_date']).daily_return.mean()
    raw_return['cum_return'] = raw_return['daily_return'].cumsum()
    raw_return['drawdown'] = raw_return['cum_return'].cummax() - raw_return['cum_return']
    #     raw_return.to_csv('%s_1227.csv'%asset_1.category_1,index=True,encoding='gbk')
    sharpe = (np.mean(raw_return['daily_return']) * 252 - 0.03) / (np.std(raw_return['daily_return']) * np.sqrt(252))
    print 'cum_return: ', raw_return['cum_return'][-1], 'max drawdown: ', np.max(
        raw_return['drawdown']), 'sharpe: ', sharpe
    plt.subplot(2, 1, 1)
    plt.plot(raw_return.index, raw_return['cum_return'], label=asset_1.category_1)
    plt.title('daily_return')
    plt.legend()
    plt.subplot(2, 1, 2)
    plt.plot(raw_return.index, raw_return['drawdown'], label=asset_1.category_1)
    plt.title('drawdown')
    plt.legend()

    ed = datetime.datetime.now()
    print ed - st
