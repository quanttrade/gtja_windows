#coding:utf8

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from WindPy import *
import copy
from sqlalchemy import create_engine
import pymysql
import warnings
warnings.filterwarnings(action='ignore')







def collect_data(category,engine):
    position_data=pd.read_sql_query("select distinct * from gtja_intern.zn_volume_data where company_name_2 in ('永安期货','新湖期货','浙商期货') "
                                    "or company_name_3 in ('永安期货','新湖期货','浙商期货') and category='%s'"%category,engine)
    date_unique=pd.read_sql("select distinct update_date from gtja_intern.%s_volume_data"%category,engine)
    position_data=position_data.iloc[:,4:]
    position_data['update_date']=pd.to_datetime(position_data['update_date'])
    date_unique['update_date']=pd.to_datetime(date_unique['update_date'])
    index_data=pd.read_csv("%sFI.csv"%category.upper(),header=0,encoding='gbk')
    index_data['update_date']=pd.to_datetime(index_data['update_date'])
    index_data=index_data.sort('update_date')
    return position_data,date_unique,index_data


def execute(category,engine):
    position_data,date_unique,index_data=collect_data(category,engine)

    ##calculate ADX
    open_yes=[np.nan]
    open_yes.extend(index_data['open'][:-1])
    index_data['open_yes']=open_yes
    high_yes=[np.nan]
    high_yes.extend(index_data['high'][:-1])
    index_data['high_yes']=high_yes
    low_yes=[np.nan]
    low_yes.extend(index_data['low'][:-1])
    index_data['low_yes']=low_yes
    close_yes=[np.nan]
    close_yes.extend(index_data['close'][:-1])
    index_data['close_yes']=close_yes
    index_data['DM+']=index_data['high']-index_data['high_yes']
    index_data['DM-']=index_data['low_yes']-index_data['low']
    index_data['TR']=map(lambda x,y,z:np.max((x,y,z)),np.abs(index_data['high']-index_data['low']),np.abs(index_data['high']-index_data['close_yes']),
                       np.abs(index_data['low']-index_data['close_yes']))
    index_data['DI+']=pd.rolling_mean(index_data['DM+'],14)/pd.rolling_mean(index_data['TR'],14)*100
    index_data['DI-']=pd.rolling_mean(index_data['DM-'],14)/pd.rolling_mean(index_data['TR'],14)*100
    index_data['ADX']=pd.rolling_mean((index_data['DI+']-index_data['DI-'])/(index_data['DI+']+index_data['DI-'])*100.,14)

    ##calculate moving average to find the trend
    index_data['MA5']=pd.rolling_mean(index_data['open'],30)
    index_data['MA10']=pd.rolling_mean(index_data['open'],60)

    index_data.index=[index_data['update_date']]
    index_data['trend']=index_data['MA5']-index_data['MA10']

    #a new table to transpose the whole matrix
    position_data_org=pd.DataFrame(columns=['company_name','position','position_chg','update_date','contract'])
    temp=position_data[['company_name_2','hold_vol_buy','hold_vol_buy_chg','update_date','contract']]
    temp=temp.rename(columns={'company_name_2':'company_name','hold_vol_buy':'position','hold_vol_buy_chg':'position_chg'})
    position_data_org=position_data_org.append(temp)
    temp=position_data[['company_name_3','hold_vol_sell','hold_vol_sell_chg','update_date','contract']]
    temp=temp.rename(columns={'company_name_3':'company_name','hold_vol_sell':'position','hold_vol_sell_chg':'position_chg'})
    temp['position']=-1*temp['position']
    position_data_org=position_data_org.append(temp)

    position_investor_zhejiang=pd.DataFrame(position_data_org.groupby(['update_date','company_name']).position.sum())
    position_investor_zhejiang=position_investor_zhejiang.reset_index()
    position_investor_zhejiang_1=position_investor_zhejiang[position_investor_zhejiang['company_name'].apply(lambda x:x.replace(' ',''))==u'新湖期货']
    position_investor_zhejiang_1.index=position_investor_zhejiang_1['update_date']
    position_investor_zhejiang_2=position_investor_zhejiang[position_investor_zhejiang['company_name'].apply(lambda x:x.replace(' ',''))==u'浙商期货']
    position_investor_zhejiang_2.index=position_investor_zhejiang_2['update_date']
    position_investor_zhejiang_3=position_investor_zhejiang[position_investor_zhejiang['company_name'].apply(lambda x:x.replace(' ',''))==u'永安期货']
    position_investor_zhejiang_3.index=position_investor_zhejiang_3['update_date']

    position_zhejiang=pd.concat([position_investor_zhejiang_1,position_investor_zhejiang_2,position_investor_zhejiang_3],axis=0)

    position_zhejiang=position_zhejiang.drop('update_date',axis=1)
    position_zhejiang=position_zhejiang.reset_index()
    position_zhejiang['update_date']=pd.to_datetime(position_zhejiang['update_date'])
    position_zhejiang=pd.merge(position_zhejiang,date_unique,on='update_date',how='outer')
    position_zhejiang_lag=pd.DataFrame()
    for i, j in position_zhejiang.groupby(['company_name']):
        j=j.sort(['update_date'])
        t=pd.DataFrame()
        t['update_date']=j['update_date'][1:]
        t['company_name']=i
        t['position']=j['position'][:-1]
        position_zhejiang_lag=position_zhejiang_lag.append(t)
    position_zhejiang_lag.index=[position_zhejiang_lag['update_date']]

    position_zhejiang_lag=position_zhejiang_lag.drop('update_date',axis=1)
    index_data=index_data.drop('update_date',axis=1)
    index_data=index_data.reset_index()
    position_zhejiang_lag=position_zhejiang_lag.reset_index()
    merged_data=pd.merge(index_data,position_zhejiang_lag,on='update_date',how='outer')

    #计算昨天与前天相比的净头寸变化量
    total_merged=pd.DataFrame()
    for i, j in merged_data.groupby('company_name'):
        j=j.sort('update_date')
        temp_list=[np.nan]
        temp_list.extend(list(j['position'][:-1]))

        j['position_lag']=temp_list
        j['position_diff']=j['position']-j['position_lag']

        total_merged=total_merged.append(j)

    position_diff_lag=[np.nan]
    position_diff_lag.extend(total_merged['position_diff'][:-1])
    total_merged['position_diff_lag']=position_diff_lag

    total_merged=total_merged.dropna(subset=['trend'],axis=0)
    # total_merged_inv=total_merged[total_merged['position_diff']>=total_merged['position_diff'].quantile(0.975)]
    total_merged['Year']=total_merged['update_date'].apply(lambda x:x.year)
    quantile_merged=pd.DataFrame(total_merged.groupby(['Year']).position_diff.quantile(0.95))
    quantile_merged=quantile_merged.rename(columns={'position_diff':'quantile_high'})
    quantile_merged.reset_index(inplace=True)
    total_merged.index=[total_merged['Year']]
    total_merged=pd.merge(total_merged,quantile_merged,on='Year',how='left')
    total_merged_inv=total_merged[total_merged['position_diff']>=total_merged['quantile_high']]

    ##用ADX来检验趋势强弱
    total_merged_inv=total_merged_inv[total_merged_inv['ADX']>=25]

    total_merged_inv['trend']=total_merged_inv['trend'].apply(lambda x:1 if x>0 else -1)

    r_long=total_merged_inv[total_merged_inv['trend']==1]
    r_long['return']=(r_long['close']-r_long['open'])/r_long['open']

    plt.figure(figsize=(20,15))
    plt.hist(total_merged['position'].dropna(),bins=50);
    plt.title('histogram of position')
    plt.show()

    # total_merged_inv=total_merged[total_merged['position_diff']<=total_merged['position_diff'].quantile(0.025)]
    quantile_merged=pd.DataFrame(total_merged.groupby(['Year']).position_diff.quantile(0.05))
    quantile_merged=quantile_merged.rename(columns={'position_diff':'quantile_low'})
    print quantile_merged['quantile_low']
    quantile_merged.reset_index(inplace=True)
    total_merged.index=[total_merged['Year']]
    total_merged=pd.merge(total_merged,quantile_merged,on='Year',how='left')
    total_merged_inv=total_merged[total_merged['position_diff']<=total_merged['quantile_low']]
    total_merged_inv=total_merged_inv[total_merged_inv['ADX']>=25]
    total_merged_inv['trend']=total_merged_inv['trend'].apply(lambda x:1 if x>0 else -1)
    r_short=total_merged_inv[total_merged_inv['trend']==-1]
    r_short['return']=-(r_short['close']-r_short['open'])/r_short['open']

    plt.figure(figsize=(40,30))
    plt.plot(position_investor_zhejiang_1.index,position_investor_zhejiang_1['position'],label=u'XinHu')
    plt.plot(position_investor_zhejiang_2.index,position_investor_zhejiang_2['position'],label=u'ZheShang')
    plt.plot(position_investor_zhejiang_3.index,position_investor_zhejiang_3['position'],label=u'YongAn')
    plt.title('position of three commodity traders')
    plt.legend()
    plt.show()

    r_long=r_long.sort('update_date')
    r_long=r_long.rename(columns={'return':'return_rate'})
    r_long_1=pd.DataFrame(r_long.groupby('update_date').return_rate.sum())
    r_long_1=r_long_1.reset_index()
    r_long_1['accu_return_rate']=100*(1+r_long_1.iloc[0,:]['return_rate'])

    for i in range(1,len(r_long_1)):
        r_long_1.iat[i,2]=r_long_1.iat[i-1,2]*(r_long_1.iat[i,1]+1)

    r_long_1.index=r_long_1['update_date']
    plt.figure(figsize=(15,10))
    plt.subplot(2,1,1)

    plt.plot(r_long_1.index,r_long_1['accu_return_rate'])
    plt.title('long accu return')
    plt.subplot(2,1,2)

    plt.plot(r_long_1.index,r_long_1['return_rate'])
    plt.title('long_return')
    plt.show()




    r_short=r_short.sort('update_date')
    r_short=r_short.rename(columns={'return':'return_rate'})
    r_short_1=pd.DataFrame(r_short.groupby('update_date').return_rate.sum())
    r_short_1=r_short_1.reset_index()
    r_short_1['accu_return_rate']=100*(1+r_short_1.iloc[0,:]['return_rate'])

    for i in range(1,len(r_short_1)):
        r_short_1.iat[i,2]=r_short_1.iat[i-1,2]*(r_short_1.iat[i,1]+1)

    r_short_1.index=r_short_1['update_date']

    plt.figure(figsize=(15,10))
    plt.subplot(2,1,1)

    plt.plot(r_short_1.index,r_short_1['accu_return_rate'])
    plt.title('short accu return')

    plt.subplot(2,1,2)
    plt.plot(r_short_1.index,r_short_1['return_rate'])
    plt.title('short return')
    plt.show()

    index_data.index=[index_data['update_date']]

    position_turn_over=pd.read_csv('C:/Users/liyuefanxxl/Documents/gtja/%s%s_turn_over.csv'%(category[0].upper(),category[1].lower()),encoding='gbk')
    position_turn_over['update_date']=pd.to_datetime(position_turn_over['update_date'])
    position_turn_over['update_date_2']=np.nan
    position_turn_over['update_date_2'][:-1]=position_turn_over['update_date'][1:]
    position_turn_over=position_turn_over.drop("update_date",axis=1)
    position_turn_over=position_turn_over.rename(columns={'update_date_2':'update_date'})

    position_turn_over=position_turn_over.dropna(subset=['turn_over_rate'],axis=0)
    position_turn_over['turn_over_rate']=abs(position_turn_over['turn_over_rate'])

    position_turn_over['Year']=position_turn_over['update_date'].apply(lambda x: x.year)
    turn_over_quantile=pd.DataFrame(position_turn_over.groupby('Year').turn_over_rate.quantile(0.95))
    turn_over_quantile.reset_index(inplace=True)
    turn_over_quantile=turn_over_quantile.rename(columns={'turn_over_rate':'quantile'})
    position_turn_over=position_turn_over.merge(turn_over_quantile,on='Year',how='left')

    position_clear_signal=position_turn_over[position_turn_over['turn_over_rate']>=position_turn_over['quantile']]
    position_clear_signal['clear_signal']=-1

    position_clear_signal.index=[position_clear_signal['update_date']]


#################################################################################
    r_long_1['invest_signal']=1
    r_long_1=r_long_1[pd.to_datetime('2011-01-01'):]
    r_long_1=pd.concat([r_long_1,position_clear_signal[['clear_signal']]],axis=1,join='outer')

    r_long_1['invest_signal']=r_long_1['invest_signal'].fillna(r_long_1['clear_signal'])



    data_long=pd.concat([r_long_1[['invest_signal']],index_data],axis=1,join='outer')


    data_long['invest_signal']=data_long['invest_signal'].fillna(method='ffill')

    data_long['invest_signal']=pd.rolling_mean(data_long['invest_signal'],2)

    data_long=data_long.dropna(subset=['invest_signal'],axis=0)

    data_long_filtered=data_long[data_long['invest_signal']>=0]

    data_long_filtered['return_rate']=np.nan
    data_long_filtered['return_rate'][1:]=np.diff(np.log(data_long_filtered['open']))


    date_unique_long=pd.DataFrame(date_unique[date_unique['update_date']>=min(data_long_filtered.index)]['update_date'])

    data_1=index_data[pd.to_datetime('2011-01-01'):]

    open_price=pd.read_csv("%s%s_5min_price.csv"%(category[0].upper(),category[1].lower()),encoding='gbk')

    open_price['update_date']=pd.to_datetime(open_price['update_date'])

    open_price['Date']=open_price['update_date'].apply(lambda x:pd.to_datetime(str(x.date())))

    open_price=open_price[open_price['update_date'].apply(lambda x:x.hour>=9 and x.minute>0)]

    open_price_1=pd.DataFrame(open_price.groupby("Date").update_date.min())

    open_price_1.reset_index(inplace=True)

    open_price_filtered=pd.merge(open_price,open_price_1[['update_date']],on='update_date',how='inner')

    open_price_filtered.index=[open_price_filtered['Date']]


    date_unique_long.index=[date_unique_long['update_date']]



    return_cal=pd.concat([open_price_filtered,data_long_filtered[['volume','invest_signal']]],axis=1,join='inner')

    return_cal['invest_signal']=pd.rolling_mean(return_cal['invest_signal'],2)

    return_cal['invest_signal']=return_cal['invest_signal'].fillna(0.5)

    open_price_list=list(np.diff(np.log(return_cal['open'])))

    open_price_list.append(np.nan)

    return_cal['return_rate']=open_price_list

    return_cal=return_cal[return_cal['invest_signal']!=0]

    accu_sum=0
    accu_list=[]
    max_draw=[np.nan]
    for item in return_cal['return_rate']:
        accu_sum+=item
        try:
            draw_benchmark=np.max(accu_list)
            max_draw.append(draw_benchmark-accu_sum)
        except:
            pass
        accu_list.append(accu_sum)

    return_cal['accu_return']=accu_list
    return_cal['max_draw']=max_draw

    plt.figure(figsize=(30,20))
    plt.plot(return_cal.index,return_cal['accu_return'])


    return_cal=return_cal.drop(['update_date'],axis=1)
    return_cal['out']=1
    signal_count=pd.concat([date_unique_long,return_cal],axis=1,join='outer')

    signal_count['out']=signal_count['out'].fillna(0)

    all_cnt=[]
    date_separator=[]
    for i in range(len(signal_count)):
        print float(i)/len(signal_count),'\r',
        temp=signal_count.iloc[i,:]

        if temp['out']==1:
            try:
                cnt+=1
            except:
                cnt=0
        elif temp['out']==0 and cnt!=0:
            try:
                all_cnt.append(cnt)
                date_separator.append(pd.to_datetime(temp['update_date']))
            except:
                pass
            cnt=0



    fig=plt.figure(facecolor='none',figsize=(15,10))
    #date_separator=list(set(data_short_filtered[data_short_filtered['invest_signal']==1].index+np.timedelta64(1,'D'))-set(data_short_filtered[data_short_filtered['invest_signal']==1].index))

    ax = fig.add_subplot(1,1,1)
    ax.plot(open_price_filtered.index,open_price_filtered['open'])
    ax.vlines(date_separator,10000,20000,colors='red')
    ax.vlines(data_long_filtered[data_long_filtered['invest_signal']==1].index,10000,20000,colors='yellow',linestyles='dashed')
    plt.show()
    print u'看多交易最大回撤：',np.max(return_cal['max_draw'])
    print u'看多交易累计收益： ', return_cal['return_rate'].sum()
    print u'看多交易单次长度： ', filter(lambda x:x!=0,all_cnt)


########################################################################################
    r_short_1['invest_signal']=1
    r_short_1=r_short_1[pd.to_datetime('2011-01-01'):]
    r_short_1=pd.concat([r_short_1,position_clear_signal[['clear_signal']]],axis=1,join='outer')

    r_short_1['invest_signal']=r_short_1['invest_signal'].fillna(r_short_1['clear_signal'])



    data_short=pd.concat([r_short_1[['invest_signal']],index_data],axis=1,join='outer')


    data_short['invest_signal']=data_short['invest_signal'].fillna(method='ffill')

    data_short['invest_signal']=pd.rolling_mean(data_short['invest_signal'],2)

    data_short=data_short.dropna(subset=['invest_signal'],axis=0)

    data_short_filtered=data_short[data_short['invest_signal']>=0]

    data_short_filtered['return_rate']=np.nan
    data_short_filtered['return_rate'][1:]=np.diff(np.log(data_short_filtered['open']))


    date_unique_short=pd.DataFrame(date_unique[date_unique['update_date']>=min(data_short_filtered.index)]['update_date'])

    data_1=index_data[pd.to_datetime('2011-01-01'):]

    open_price=pd.read_csv("%s%s_5min_price.csv"%(category[0].upper(),category[1].lower()),encoding='gbk')

    open_price['update_date']=pd.to_datetime(open_price['update_date'])

    open_price['Date']=open_price['update_date'].apply(lambda x:pd.to_datetime(str(x.date())))

    open_price=open_price[open_price['update_date'].apply(lambda x:x.hour>=9 and x.minute>0)]

    open_price_1=pd.DataFrame(open_price.groupby("Date").update_date.min())





    date_unique_short.index=[date_unique_short['update_date']]



    open_price_1.reset_index(inplace=True)

    open_price_filtered=pd.merge(open_price,open_price_1[['update_date']],on='update_date',how='inner')

    open_price_filtered.index=[open_price_filtered['Date']]

    return_cal=pd.concat([open_price_filtered,data_short_filtered[['volume','invest_signal']]],axis=1,join='inner')

    return_cal['invest_signal']=pd.rolling_mean(return_cal['invest_signal'],2)

    return_cal['invest_signal']=return_cal['invest_signal'].fillna(0.5)

    open_price_list=list(-np.diff(np.log(return_cal['open'])))

    open_price_list.append(np.nan)

    return_cal['return_rate']=open_price_list

    return_cal=return_cal[return_cal['invest_signal']!=0]

    accu_sum=0
    accu_list=[]
    max_draw=[np.nan]
    for item in return_cal['return_rate']:
        accu_sum+=item
        try:
            draw_benchmark=np.max(accu_list)
            max_draw.append(draw_benchmark-accu_sum)
        except:
            pass
        accu_list.append(accu_sum)

    return_cal['accu_return']=accu_list
    return_cal['max_draw']=max_draw


    plt.figure(figsize=(30,20))
    plt.plot(return_cal.index,return_cal['accu_return'])




    return_cal=return_cal.drop(['update_date'],axis=1)
    return_cal['out']=1
    signal_count=pd.concat([date_unique_short,return_cal],axis=1,join='outer')

    signal_count['out']=signal_count['out'].fillna(0)

    all_cnt=[]
    date_separator=[]
    for i in range(len(signal_count)):
        print float(i)/len(signal_count),'\r',
        temp=signal_count.iloc[i,:]

        if temp['out']==1:
            try:
                cnt+=1
            except:
                cnt=0
        elif temp['out']==0 and cnt!=0:
            try:
                all_cnt.append(cnt)
                date_separator.append(pd.to_datetime(temp['update_date']))
            except:
                pass
            cnt=0


    fig=plt.figure(facecolor='none',figsize=(15,10))
    #date_separator=list(set(data_short_filtered[data_short_filtered['invest_signal']==1].index+np.timedelta64(1,'D'))-set(data_short_filtered[data_short_filtered['invest_signal']==1].index))

    ax = fig.add_subplot(1,1,1)
    ax.plot(open_price_filtered.index,open_price_filtered['open'])
    ax.vlines(date_separator,10000,20000,colors='red')
    ax.vlines(data_short_filtered[data_short_filtered['invest_signal']==1].index,10000,20000,colors='yellow',linestyles='dashed')
    plt.show()
    print u'看空交易最大回撤：',np.max(return_cal['max_draw'])
    print u'看空交易累计收益： ', return_cal['return_rate'].sum()
    print u'看空交易单次长度： ', filter(lambda x:x!=0,all_cnt)



if __name__=='__main__':
    engine = create_engine("mysql+pymysql://liyuefan:1994050306@localhost/gtja_intern?charset=utf8")
    category='zn'
    execute(category,engine)