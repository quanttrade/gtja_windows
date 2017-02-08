# coding: utf-8

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import warnings

warnings.filterwarnings(action='ignore')


def execute(category):
    df = pd.read_csv('/Users/liyuefan/Documents/gtja/%sFI_0112.csv' % category, encoding='gbk')

    df['update_date'] = pd.to_datetime(df['update_date'])
    df['close_yes'] = df['close'].shift(1)

    df['ma10'] = pd.rolling_mean(df['close_yes'], 10)
    df['ma20'] = pd.rolling_mean(df['close_yes'], 20)
    df['ma30'] = pd.rolling_mean(df['close_yes'], 60)
    df['ma60'] = pd.rolling_mean(df['close_yes'], 100)
    df['ma100'] = pd.rolling_mean(df['close_yes'], 200)

    df['close_return_yes'] = np.log(df['close_yes'])
    df['close_return_yes'] = df['close_return_yes'].diff()
    df['volatility_20'] = pd.rolling_std(df['close_return_yes'], 20)
    df['volatility_60'] = pd.rolling_std(df['close_return_yes'], 60)
    df['volatility_100'] = pd.rolling_std(df['close_return_yes'], 100)
    df['volatility_200'] = pd.rolling_std(df['close_return_yes'], 200)

    def sig(x1, p):
        if p < x1:
            return -1
        elif p > x1:
            return 1
        else:
            return np.nan

            #     df['stop_ma10']=map(sig,df['ma10'],df['close'])

    df['p_ma10'] = map(sig, df['ma20'], df['close'])
    df['p_ma30'] = map(sig, df['ma30'], df['close'])
    df['p_ma60'] = map(sig, df['ma60'], df['close'])
    df['p_ma100'] = map(sig, df['ma100'], df['close'])

    def dir(x):
        if x > 0:
            return 1
        elif x < 0:
            return -1
        else:
            return 0

    df = df.sort('update_date')

    df['p_ma10'] = df['p_ma10'].fillna(method='ffill')
    df['p_ma30'] = df['p_ma30'].fillna(method='ffill')
    df['p_ma60'] = df['p_ma60'].fillna(method='ffill')
    df['p_ma100'] = df['p_ma100'].fillna(method='ffill')

    df = df.dropna(axis=0)

    pos_mat = df.loc[:, ['p_ma10', 'p_ma30', 'p_ma60', 'p_ma100', 'volatility_20', 'volatility_60', 'volatility_100',
                         'volatility_200']]
    pos_mat = pos_mat.as_matrix()

    N = pos_mat.shape[0]
    p = np.zeros(N)
    temp_tag = 0
    for i in range(N):
        if np.isnan(pos_mat[i, 3]) == True:
            p[i] = 0
        else:
            if pos_mat[i, 0] > 0:
                temp_tag = 1
                dis_20 = pos_mat[i, 4] / np.mean(pos_mat[:i, 4])
                dis_60 = pos_mat[i, 5] / np.mean(pos_mat[:i, 5])
                dis_100 = pos_mat[i, 6] / np.mean(pos_mat[:i, 6])
                dis_200 = pos_mat[i, 7] / np.mean(pos_mat[:i, 7])
                p[i] = 0.4 / dis_20
                if pos_mat[i, 3] > 0:
                    p[i] = (0.4 / dis_20 + 0.3 / dis_60 + 0.2 / dis_100 + 0.1 / dis_200)
                elif pos_mat[i, 2] > 0:
                    p[i] = (0.4 / dis_20 + 0.3 / dis_60 + 0.2 / dis_100)
                elif pos_mat[i, 1] > 0:
                    p[i] = (0.4 / dis_20 + 0.3 / dis_60)

            elif pos_mat[i, 0] < 0:
                temp_tag = -1
                dis_20 = pos_mat[i, 4] / np.mean(pos_mat[:i, 4])
                dis_60 = pos_mat[i, 5] / np.mean(pos_mat[:i, 5])
                dis_100 = pos_mat[i, 6] / np.mean(pos_mat[:i, 6])
                dis_200 = pos_mat[i, 7] / np.mean(pos_mat[:i, 7])
                p[i] = -0.4 / dis_20
                if pos_mat[i, 3] < 0:
                    p[i] = (-0.4 / dis_20 - 0.3 / dis_60 - 0.2 / dis_100 - 0.1 / dis_200)
                elif pos_mat[i, 2] < 0:
                    p[i] = (-0.4 / dis_20 - 0.3 / dis_60 - 0.2 / dis_100)
                elif pos_mat[i, 1] < 0:
                    p[i] = (-0.4 / dis_20 - 0.3 / dis_60)

                    #         elif temp_tag>0 and pos_mat[i,8]==-1:
                    #             temp_tag=0
                    #             print 'stop'
                    #             p[i]=0
                    #         elif temp_tag<0 and pos_mat[i,8]==1:
                    #             temp_tag=0
                    #             print 'stop'
                    #             p[i]=0
            else:
                p[i] = np.nan

    df['position'] = p
    df['position'] = df['position'].fillna(method='ffill')

    df['close_return'] = np.log(df['close'])
    df['close_return'] = df['close_return'].diff()

    df['position'] = df['position'].shift(2)

    df['daily_return'] = df['position'] * df['close_return']

    close_return = np.array(df['daily_return'])
    position = np.array(df['position'])
    for i in range(1, len(position)):
        if position[i] != position[i - 1]:
            close_return[i - 1] = close_return[i - 1] - 1. / 10000
            close_return[i] = close_return[i] - 1. / 10000
        else:
            pass
    df['daily_return'] = close_return

    df['cum_return'] = df['daily_return'].cumsum()

    df.index = [df['update_date']]
    return df

# 这一版是按照动量原理来进行资产组合，ranking period取12个月，holding period取1个月


def comp_select(asset_pool):
    df=pd.DataFrame()
    N=1
    for a in asset_pool:
        tmp=execute(a)
        tmp=tmp[['update_date','close_return']]
        tmp.index=[tmp['update_date']]
        tmp=tmp.drop(['update_date'],axis=1)
        tmp=tmp.rename(columns={'close_return':a})
        df=pd.concat([df,tmp],axis=1,join='outer')
    df['update_date']=df.index
    df=df.sort()
    df['date_tag']=df['update_date'].apply(lambda x: str(x.year)+'-0'+str(x.month) if len(str(x.month))==1 else str(x.year)+'-'+str(x.month))
    df_mean=df.groupby(['date_tag']).mean()
    df_mean_tmp=pd.rolling_sum(df_mean,N)
    df_mean_tmp=df_mean_tmp.shift(1)
    df_mean_tmp=df_mean_tmp.iloc[N:,:]
    date_list=df_mean_tmp.index
    comp_list=df_mean_tmp.columns
    mat=df_mean_tmp.as_matrix()
    m=mat.shape[0]
    comp_dict={}
    for j in range(m):
        tmp=mat[j,:]
        cp_l=[comp_list[i] for i in range(len(comp_list)) if np.isnan(tmp[i])==False]
        tmp=filter(lambda x: np.isnan(x)==False,tmp)
        comp_long=cp_l[np.argmax(tmp)]

        comp_short=cp_l[np.argmin(tmp)]
        comp_dict[date_list[j]]=(comp_long,comp_short)
    return comp_dict

# 构建组合计算
def port(comp_dict):
    item_list=comp_dict.items()
    df_total=pd.DataFrame()
    for item in item_list:
        d_t=item[0]
        print d_t,comp_dict[item[0]]
        d_c=item[1]
        comp_l=d_c[0]
        comp_s=d_c[1]
        comp_l=execute(comp_l)
        comp_s=execute(comp_s)
        comp_l['date_tag']=comp_l['update_date'].apply(lambda x: str(x.year)+'-0'+str(x.month) if len(str(x.month))==1 else str(x.year)+'-'+str(x.month))
        comp_s['date_tag']=comp_s['update_date'].apply(lambda x: str(x.year)+'-0'+str(x.month) if len(str(x.month))==1 else str(x.year)+'-'+str(x.month))
        comp_l=comp_l[comp_l['date_tag']==d_t]
        comp_s=comp_s[comp_s['date_tag']==d_t]
        comp_l=comp_l[['update_date','close_return','daily_return']]
        comp_s=comp_s[['update_date','close_return','daily_return']]
        comp_l=comp_l.rename(columns={'close_return':'close_return_1','daily_return':'daily_return_1'})
        comp_s=comp_s.rename(columns={'close_return':'close_return_2','daily_return':'daily_return_2'})
        comp_all=pd.merge(comp_l,comp_s,on='update_date',how='inner')
        comp_all['port_return']=0.5*comp_all['daily_return_1']+0.5*comp_all['daily_return_2']
        comp_all['port_close']=0.5*comp_all['close_return_1']+0.5*comp_all['close_return_2']
        df_total=df_total.append(comp_all)
    return df_total

if __name__=='__main__':
    asset_pool=['CU','ZN','PB','AL','NI','I','JM','J','WH','ZC','Y','TA','SR','RU','RM','P','M','C']
    comp_dict=comp_select(asset_pool)
    print 'port selected...'
    df=port(comp_dict)
    print 'port constructed...'
    df=df.sort(['update_date'])
    df['cum_return']=df['port_return'].cumsum()
    print 'plotting...'
    plt.figure(figsize=(8,4))
    plt.plot(df['update_date'],df['cum_return'])
    plt.show()
