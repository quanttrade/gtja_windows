#! /Users/liyuefan/anaconda2/bin/python
#  coding: utf-8


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import copy
from sqlalchemy import create_engine
import pymysql
import warnings
import random
from HMM_Cal import execute
warnings.filterwarnings(action='ignore')




class gtjaCommodity(object):
    def __init__(self,brokerName,engine,category,data_source):
        self.brokerName=brokerName
        self.engine=engine
        self.category=category
        self.data_source=data_source

    def collectData(self):


        if len(self.category)>1:
            self.category_1=self.category[0].upper()+self.category[1:].lower()
        elif len(self.category)==1:
            self.category_1=copy.deepcopy(self.category)
            self.category_1=self.category.upper()
        else:
            raise Exception("parameter error!")

        print self.category_1


        for i in range(len(self.brokerName)):
            if len(self.brokerName)>1:
                if i==0:
                    self.brokerNameParenth='('+'\''+self.brokerName[i].encode('utf8')+'\''+','
                elif i>0 and i<len(self.brokerName)-1:
                    self.brokerNameParenth+='\''+self.brokerName[i].encode('utf8')+'\''+','
                else:
                    self.brokerNameParenth+='\''+self.brokerName[i].encode('utf8')+'\''+')'
            else:
                self.brokerNameParenth='('+'\''+self.brokerName[i].encode('utf8')+'\''+')'


        print "select distinct * from gtja_intern.%s_volume_data where company_name_2 in %s or company_name_3 in %s and contract='全部合约'"%(self.category,self.brokerNameParenth,self.brokerNameParenth)

        if self.data_source=='dalian':
            position_data=pd.read_sql_query("select distinct * from gtja_intern.%s_volume_data where company_name_2 in %s "
                                            "or company_name_3 in %s and contract='全部合约'"%(self.category,self.brokerNameParenth,self.brokerNameParenth),self.engine)
        elif self.data_source=='shanghai':
            position_data=pd.read_sql_query("select distinct * from gtja_intern.%s_volume_data where company_name_2 in %s "
                                            "or company_name_3 in %s and category='%s'"%(self.category,self.brokerNameParenth,self.brokerNameParenth,self.category),self.engine)
        date_unique=pd.read_sql("select distinct update_date from gtja_intern.%s_volume_data"%self.category,self.engine)
        position_data=position_data.iloc[:,4:]
        position_data['update_date']=pd.to_datetime(position_data['update_date'])
        if self.data_source=='dalian':
            position_data['hold_vol_buy']=position_data['hold_vol_buy'].apply(lambda x:float(x.replace(',','')) if x!=u'\xa0' else np.nan)
            position_data['hold_vol_buy_chg']=position_data['hold_vol_buy_chg'].apply(lambda x:float(x.replace(',','')) if x!=u'\xa0' else np.nan)
            position_data['hold_vol_sell']=position_data['hold_vol_sell'].apply(lambda x:float(x.replace(',','')) if x!=u'\xa0' else np.nan)
            position_data['hold_vol_sell_chg']=position_data['hold_vol_sell_chg'].apply(lambda x:float(x.replace(',','')) if x!=u'\xa0' else np.nan)
            position_data['company_name_2']=position_data['company_name_2'].apply(lambda x:x.replace(' ',''))
            position_data['company_name_3']=position_data['company_name_3'].apply(lambda x:x.replace(' ',''))
        elif self.data_source=='shanghai':
            position_data['hold_vol_buy']=position_data['hold_vol_buy'].apply(lambda x:float(x) if x!=u'\xa0' else np.nan)
            position_data['hold_vol_buy_chg']=position_data['hold_vol_buy_chg'].apply(lambda x:float(x) if x!=u'\xa0' else np.nan)
            position_data['hold_vol_sell']=position_data['hold_vol_sell'].apply(lambda x:float(x) if x!=u'\xa0' else np.nan)
            position_data['hold_vol_sell_chg']=position_data['hold_vol_sell_chg'].apply(lambda x:float(x) if x!=u'\xa0' else np.nan)
            position_data['company_name_2']=position_data['company_name_2'].apply(lambda x:x.replace(' ',''))
            position_data['company_name_3']=position_data['company_name_3'].apply(lambda x:x.replace(' ',''))
        date_unique['update_date']=pd.to_datetime(date_unique['update_date'])
        index_data=pd.read_csv("%sFI.csv"%self.category.upper(),header=0,encoding='gbk')
        index_data['update_date']=pd.to_datetime(index_data['update_date'])
        index_data=index_data.sort('update_date')



        open_price=pd.read_csv("%s_5min_price.csv"%(self.category_1),encoding='gbk')

        open_price['update_date']=pd.to_datetime(open_price['update_date'])

        open_price['Date']=open_price['update_date'].apply(lambda x:pd.to_datetime(str(x.date())))

        open_price=open_price[open_price['update_date'].apply(lambda x:x.hour>=9 and x.minute>0)]

        open_price_1=pd.DataFrame(open_price.groupby("Date").update_date.min())

        open_price_1.reset_index(inplace=True)

        open_price_filtered=pd.merge(open_price,open_price_1[['update_date']],on='update_date',how='inner')

        open_price_filtered=open_price_filtered.drop(['update_date'],axis=1)
        open_price_filtered=open_price_filtered.rename(columns={'Date':'update_date'})


        position_turn_over=pd.read_csv('%s_turn_over.csv'%(self.category_1),encoding='gbk')
        position_turn_over['update_date']=pd.to_datetime(position_turn_over['update_date'])

        return position_data,date_unique,index_data,open_price_filtered,position_turn_over

    def oneOrderLag(self,data,columnsFrom,columnsTo):
        for colf,colt in zip(columnsFrom,columnsTo):
            oneLag=[np.nan]
            oneLag.extend(data[colf][:-1])
            data[colt]=oneLag
        return data

    def ADX(self):
        self.index_data=self.oneOrderLag(self.index_data,['open','high','low','close'],['open_yes','high_yes','low_yes','close_yes'])
        self.index_data['DM+']=self.index_data['high']-self.index_data['high_yes']
        self.index_data['DM-']=self.index_data['low_yes']-self.index_data['low']
        self.index_data['TR']=map(lambda x,y,z: np.max((x,y,z)),np.abs(self.index_data['high']-self.index_data['low']),
                                                                 np.abs(self.index_data['high']-self.index_data['close_yes']),
                                                                 np.abs(self.index_data['low']-self.index_data['close_yes']))
        self.index_data['DI+']=pd.rolling_mean(self.index_data['DM+'],14)/pd.rolling_mean(self.index_data['TR'],14)*100
        self.index_data['DI-']=pd.rolling_mean(self.index_data['DM-'],14)/pd.rolling_mean(self.index_data['TR'],14)*100
        self.index_data['ADX']=pd.rolling_mean((self.index_data['DI+']-self.index_data['DI-'])/
                                               (self.index_data['DI+']+self.index_data['DI-'])*100,14)
        return self.index_data

    def filterData(self):


        self.position_data,self.date_unique,self.index_data,self.open_price,self.position_turn_over=self.collectData()

        #######################################################################################
        #index_data
        ##calculate ADX
        self.index_data=self.ADX()


        ##calculate moving average to find the trend
        self.index_data['MA5']=pd.rolling_mean(self.index_data['close'],30)
        self.index_data['MA10']=pd.rolling_mean(self.index_data['close'],60)

        ##calculate moving min of last 5 days
        self.index_data['min5']=pd.rolling_min(self.index_data['low'],5)
        self.index_data['max5']=pd.rolling_max(self.index_data['high'],5)


        self.index_data['trend']=self.index_data['MA5']-self.index_data['MA10']
        trend_diff=[np.nan]
        trend_diff.extend(np.diff(self.index_data['trend']))
        self.index_data['trend_diff']=trend_diff
        position_all_diff=[np.nan]
        position_all_diff.extend(np.diff(self.index_data['position_all']))


        self.index_data['position_all_diff']=position_all_diff
        self.index_data=self.oneOrderLag(self.index_data,['min5','max5','trend','trend_diff','MA5','MA10','position_all','position_all_diff'],['min5','max5','trend','trend_diff','MA5','MA10','position_all','position_all_diff'])


        self.index_data['trend']=map(execute,self.index_data['update_date'])

        #################################################################################
        #position_data
        #a new table to transpose the whole matrix
        self.position_data_org=pd.DataFrame(columns=['company_name','position','position_chg','update_date','contract'])
        temp=self.position_data[['company_name_2','hold_vol_buy','hold_vol_buy_chg','update_date','contract']]
        temp=temp.rename(columns={'company_name_2':'company_name','hold_vol_buy':'position','hold_vol_buy_chg':'position_chg'})
        temp['direction_tag']=temp['position_chg'].apply(lambda x:10 if x>0 else 0)
        self.position_data_org=self.position_data_org.append(temp)
        temp=self.position_data[['company_name_3','hold_vol_sell','hold_vol_sell_chg','update_date','contract']]
        temp=temp.rename(columns={'company_name_3':'company_name','hold_vol_sell':'position','hold_vol_sell_chg':'position_chg'})
        temp['position']=-1*temp['position']
        temp['position_chg']=-1*temp['position_chg']
        temp['direction_tag']=temp['position_chg'].apply(lambda x:1 if x<0 else 0)
        self.position_data_org=self.position_data_org.append(temp)


        ##sum one broker's net position in one day together
        self.position_data_org_2=self.position_data_org.groupby(['update_date','company_name']).sum()
        try:
            self.position_data_org_2=self.position_data_org_2.drop(['contract'],axis=1)
            self.position_data_org_1=self.position_data_org.groupby(['update_date','company_name']).contract.count()
            self.position_data_org=pd.concat([self.position_data_org_2,self.position_data_org_1],axis=1,join='inner')
            self.position_data_org=self.position_data_org.loc[:,['position','position_chg','direction_tag','contract']]
        except:
            self.position_data_org=self.position_data_org_2
            self.position_data_org['contract']=1
        self.position_data_org.reset_index(inplace=True)


        #取出特定交易商的交易持仓变化记录
        self.position_data_selected=pd.DataFrame(columns=self.position_data_org.columns)
        for item in self.brokerName:
            print item
            temp=self.position_data_org[self.position_data_org['company_name']==item]
            if len(temp)!=0:
                self.position_data_selected=self.position_data_selected.append(temp)
            else:
                print 'cannot find %s in data, please check...'%item


        #将全量日期对上筛选后的数据
        self.position_data_selected=pd.merge(self.date_unique,self.position_data_selected,on=['update_date'],how='left')
        ##将今天收盘得到的数据设定为明天的决策依据
        self.position_data_lagged=pd.DataFrame()
        for i,j in self.position_data_selected.groupby('company_name'):
            j=j.sort('update_date')
            j=self.oneOrderLag(j,['position','position_chg','direction_tag'],['position','position_chg','direction_tag'])
            self.position_data_lagged=self.position_data_lagged.append(j)

        #############################################################
        #position_turn_over数据处理
        #position_turn_over中的数据也需要进行时间轴的平移，比如1月1号的换手率数据被用于2号的平仓决策过程
        self.position_turn_over=self.oneOrderLag(self.position_turn_over,['turn_over_rate'],['turn_over_rate'])
        self.position_turn_over=self.position_turn_over.loc[:,['update_date','turn_over_rate']]
        self.position_turn_over['turn_over_rate']=self.position_turn_over['turn_over_rate'].apply(abs)

        return self.index_data,self.position_data_lagged,self.position_turn_over


    def makeDecisionStart(self,ratio_high,ratio_low,how,index_data,position_data_lagged,position_turn_over):
        ##计算收益率，因为开盘建仓，所以需要计算的是比如1月1号发出建仓指令，那么从计算1月1号到2号之间的收益率开始
        # self.index_data,self.position_data_lagged,self.position_turn_over=self.filterData()

        self.index_data=index_data
        self.position_data_lagged=position_data_lagged
        self.position_turn_over=position_turn_over
        self.index_data=self.index_data.drop(['open'],axis=1)
        tableForCal=pd.merge(self.index_data,self.open_price[['open','update_date']],on=['update_date'],how='left')
        tableForCal['open_high']=(tableForCal['high']-tableForCal['open'])/tableForCal['open']
        tableForCal['open_low']=(tableForCal['low']-tableForCal['open'])/tableForCal['open']
        tableForCal=pd.merge(tableForCal,self.position_data_lagged,on=['update_date'],how='left')
        total_temp=pd.DataFrame()
        for i,j in tableForCal.groupby(['company_name']):
            j=j.sort(['update_date'])
            return_rate=list(np.diff(np.log(j['open']))[:])
            return_rate.append(np.nan)
            j['return_rate']=return_rate
            if how=='quantile':
                j['position_quantile']=j['position'].rolling(500).quantile(ratio_high)
            elif how=='percent':
                j['position_quantile']=np.nan
            total_temp=total_temp.append(j)
        tableForCal=total_temp
        #每日收益率计算规则为一旦发出开场信号，则当天收益率计算进入总收益率，如果发出平仓信号，当天不计入

        #先判定trend项是否符合开仓条件
        tableForCal['trend']=tableForCal['trend'].apply(lambda x: 1 if x>0 else -1)
        #判定仓位变化能否符合开仓条件，需要通过仓位变化方向（空头且增加，多头且增加）
        #看多

        tableForCal['pos_all_ratio']=tableForCal['position_chg']/tableForCal['position_all']
        tableForCal['chg_all_ratio_quantile']=tableForCal['pos_all_ratio'].rolling(250).quantile(ratio_high)

        if how=='percent':
            tableForCalLong=tableForCal[tableForCal['position_chg']>=tableForCal['chg_all_ratio_quantile']*tableForCal['position_all']]
        elif how=='quantile':
            tableForCalLong=tableForCal[tableForCal['position_chg']>=tableForCal['position_quantile']]

        def dir_tag(x):
            x=int(x)
            if x/10>0 and x%10==0:
                return 1
            elif x/10==0 and x%10>0:
                return -1

        tableForCalLong=tableForCalLong[tableForCalLong['direction_tag'].apply(dir_tag)==1]
        tableForCalLong['start_signal']=tableForCalLong['trend'].apply(lambda x:1 if x>0 else np.nan)

        #看空
        if how=='percent':
            tableForCalShort=tableForCal[tableForCal['position_chg']<=-tableForCal['chg_all_ratio_quantile']*tableForCal['position_all']]
        elif how=='quantile':
            tableForCalShort=tableForCal[tableForCal['position_chg']<=-tableForCal['position_quantile']]
        tableForCalShort=tableForCalShort[tableForCalShort['direction_tag'].apply(dir_tag)==-1]
        tableForCalShort['start_signal']=tableForCalShort['trend'].apply(lambda x: -1 if x<0 else np.nan)

        tableForCalStart_=tableForCalShort.append(tableForCalLong)

        tableForCalStart=pd.merge(tableForCal,tableForCalStart_[['update_date','company_name','start_signal']],on=['update_date','company_name'],how='left')

        return tableForCalStart

    def makeDecisionStop(self,ratio_stop):
        tableForCalStart=self.stopLossTrailing(0.2)
        self.position_turn_over['turn_over_quantile']=self.position_turn_over['turn_over_rate'].rolling(window=250).quantile(ratio_stop)
        self.position_turn_over=self.position_turn_over[self.position_turn_over['turn_over_rate']>=self.position_turn_over['turn_over_quantile']]
        self.position_turn_over['stop_signal']=0
        self.tableForCalAll=pd.merge(tableForCalStart,self.position_turn_over,on=['update_date'],how='left')
        self.tableForCalTotal=pd.DataFrame()
        for i,j in self.tableForCalAll.groupby(['company_name']):

            # self.tableForCalAll['start_signal']=self.tableForCalAll['start_signal'].fillna(method='ffill')
            # self.tableForCalAll['stop_signal']=self.tableForCalAll['stop_signal'].fillna(1)
            j=j.sort(['update_date'])
            j['trade_signal']=j['trade_signal'].fillna(j['stop_signal'])
            j['trade_signal']=j['trade_signal'].fillna(j['start_signal'])

            j['trade_signal']=j['trade_signal']+j['trend']
            j['trade_signal']=j['trade_signal']/2.
            def convert(x):
                if x==1 or x==-1:
                    return x
                elif np.isnan(x)==False:
                    return 0
                else:
                    return np.nan
            j['trade_signal']=j['trade_signal'].apply(convert)
            tag=np.nan
            for k in range(len(j)):
                if np.isnan(j.iloc[k,:]['trade_signal'])==False:
                    tag=j.iloc[k,:]['trade_signal']
                elif tag*j.iloc[k,:]['trend']<0:
                    j.iloc[k,list(j.columns).index(u'trade_signal')]=0
                else:
                    pass
            j['trade_signal']=j['trade_signal'].fillna(method='ffill')
            self.tableForCalTotal=self.tableForCalTotal.append(j)
        return self.tableForCalTotal

    def returnCal(self):
        self.tableForCalTotal=self.makeDecisionStop(0.95)
        self.tableForCalTotal['trade_signal']=self.tableForCalTotal['trade_signal'].apply(lambda x: 1 if x>0 else x)
        self.tableForCalTotal['trade_signal']=self.tableForCalTotal['trade_signal'].apply(lambda x: -1 if x<0 else x)
        self.tableForCalTotal['daily_return_without_stop']=self.tableForCalTotal['return_rate']*self.tableForCalTotal['trade_signal']
        self.tableForCalTotal['daily_return']=self.tableForCalTotal['daily_return'].fillna(self.tableForCalTotal['daily_return_without_stop'])
        # print self.tableForCalTotal['daily_return'].sum()
        return self.tableForCalTotal

    def sampleSep(self,data,train_ratio):
        totalSample=data
        totalSample=totalSample.dropna(subset=['return_rate'],axis=0)
        period=pd.unique(totalSample['update_date'])
        period=period.sort(['update_date'])
        sep_point=period[int(train_ratio*len(period))]
        train_sample=totalSample[totalSample['update_date']<=sep_point]
        test_sample=totalSample[totalSample['update_date']>sep_point]
        return train_sample,test_sample


    def crossValidation(self):
        tableForCalTotal=self.returnCal()
        train_sample=self.sampleSep(tableForCalTotal,train_ratio=0.7)


    def stopLossTrailing(self,threshold):
        self.index_data,self.position_data_lagged,self.position_turn_over=self.filterData()
        returnCal=self.makeDecisionStart(0.95,0.95,'percent',self.index_data,self.position_data_lagged,self.position_turn_over)
        returnCalAll=pd.DataFrame()
        for i,j in returnCal.groupby(['company_name']):
            j=j.sort('update_date')
            j['signal_for_stoploss_cal']=j['start_signal'].fillna(method='ffill')
            j['daily_loss_max_long']=j['open_low']*j['signal_for_stoploss_cal']
            j['daily_loss_max_short']=j['open_high']*j['signal_for_stoploss_cal']

            returnCal_long=j[j['signal_for_stoploss_cal']==1]
            returnCal_long['trade_signal']=returnCal_long['daily_loss_max_long'].apply(lambda x:0 if x<=-threshold else np.nan)
            returnCal_long['return_rate_stoploss']=-threshold+returnCal_long['trade_signal']
            returnCal_long['daily_return']=returnCal_long['return_rate_stoploss']

            returnCal_short=j[j['signal_for_stoploss_cal']==-1]
            returnCal_short['trade_signal']=returnCal_short['daily_loss_max_short'].apply(lambda x:0 if x<=-threshold else np.nan)
            returnCal_short['return_rate_stoploss']=-threshold+returnCal_short['trade_signal']
            returnCal_short['daily_return']=returnCal_short['return_rate_stoploss']

            j_all=returnCal_long.append(returnCal_short)
            returnCalAll=returnCalAll.append(j_all)
        return returnCalAll


    def maxDrawdown(self):
        returnCal=self.returnCal()
        returnCal['update_date']=pd.to_datetime(returnCal['update_date'])

        drawDown=returnCal.loc[:,['update_date','daily_return','trade_signal']]
        drawDown=drawDown.groupby('update_date').sum()
        drawDown['daily_return']=drawDown['daily_return']/drawDown['trade_signal'].apply(np.abs)
        drawDown['daily_return']=drawDown['daily_return'].apply(lambda x: 0 if x==np.inf or x==-np.inf else x)
        drawDown['trade_signal']=drawDown['trade_signal']/drawDown['trade_signal'].apply(np.abs)
        drawDown['daily_return']=drawDown['daily_return'].fillna(0)
        print drawDown['daily_return'].sum()

        drawDown['cum_return']=drawDown['daily_return'].cumsum()
        drawDown['max_return']=drawDown['cum_return'].cummax()
        drawDown['max_drawdown']=drawDown['max_return']-drawDown['cum_return']
        drawDown=drawDown.dropna(axis=0)
        drawDown=drawDown[pd.to_datetime('2015-01-01'):]
        returnCal=returnCal[returnCal['update_date']>=pd.to_datetime('2015-01-01')]
        returnCal.index=[returnCal['update_date']]
        print drawDown['max_drawdown'].max()
        plt.subplot(5,1,1)
        plt.plot(drawDown['cum_return'])
        plt.subplot(5,1,2)
        plt.bar(drawDown.index,drawDown['trade_signal'])
        plt.subplot(5,1,3)
        plt.plot(drawDown['daily_return'])
        plt.subplot(5,1,4)
        plt.plot(returnCal['open'])
        plt.plot(returnCal['MA5'],label='ma5')
        plt.plot(returnCal['MA10'],label='ma10')
        # plt.legend()
        plt.subplot(5,1,5)
        plt.bar(returnCal.index,returnCal['position_chg'])
        plt.plot(returnCal.index,returnCal['chg_all_ratio_quantile']*returnCal['position_all'])
        plt.plot(returnCal.index,-returnCal['chg_all_ratio_quantile']*returnCal['position_all'])
        plt.savefig('zn_result.png')
        plt.show()
        return drawDown






if __name__=='__main__':

    engine = create_engine("mysql+pymysql://liyuefan:1994050306@localhost/gtja_intern?charset=utf8")
    asset=gtjaCommodity([u'新湖期货',u'永安期货',u'浙商期货'],engine,'i','dalian')
    asset.maxDrawdown()









