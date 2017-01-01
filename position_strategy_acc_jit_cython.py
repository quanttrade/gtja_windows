#! /Users/liyuefan/anaconda2/bin/python
#  coding: utf-8


import pandas as pd
import numpy as np
import copy
from sqlalchemy import create_engine
import pymysql
import warnings
import wrapt
import time
from numba import jit
import stop_loss
import stop_signal
from HMM_Cal import execute
warnings.filterwarnings(action='ignore')

@wrapt.decorator
def timeit(func, instance, args, kwargs):
    t=time.time()
    ans=func(*args, **kwargs)
    t=time.time()-t
    print func.__name__, t
    return ans


@jit
def sep_trade(trade_signal):
    cnt=0
    N=len(trade_signal)
    cnt_l=np.zeros(N)
    for i in range(1,N):
        if np.isnan(trade_signal[i])==False and trade_signal[i]!=0:
            if trade_signal[i]!=trade_signal[i-1]:
                cnt+=1
                cnt_l[i]=cnt
            else:
                cnt_l[i]=cnt
        else:
            cnt_l[i]=np.nan
    return cnt_l
@timeit
@jit
def stop(data,start_signal,stop_signal_1,stop_signal_2):
    N=len(data)
    st_sig=np.nan
    ex=np.empty(N)
    for i in range(N):
        if np.isnan(data[i,start_signal])==False:
            st_sig=data[i,start_signal]
            ex[i]=np.nan
        elif np.isnan(st_sig)==False and data[i,stop_signal_1]!=st_sig:
            ex[i]=0
        elif np.isnan(st_sig)==False and np.isnan(data[i,stop_signal_2])==False and data[i,stop_signal_2]!=st_sig:
            ex[i]=0
        else:
            ex[i]=np.nan
    return ex


class gtja_commodity(object):

    #初始化参数，包括跟踪的期货商的名称（list），数据库连接，期货品种，数据来源（大连或上海）
    def __init__(self,brokerName,engine,category,data_source):
        self.brokerName=brokerName
        self.engine=engine
        self.data_source=data_source
        self.category=category



    #加载数据
    @timeit
    def load_data(self):
        #将品种字段改成符合数据文件命名规则的大小写，方便之后从csv和数据库中提取数据
        if len(self.category)>1:
            self.category_1=self.category[0].upper()+self.category[1:].lower()
        elif len(self.category)==1:
            self.category_1=copy.deepcopy(self.category)
            self.category_1=self.category.upper()
        else:
            raise Exception("parameter error!")

        print self.category_1


        #将期货商list重新改写成符合sql查询语句语法的字符串
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

        #从sql数据库提取数据
        if self.data_source=='dalian':
            position_data=pd.read_sql_query("select distinct * from gtja_intern.%s_volume_data where company_name_2 in %s "
                                            "or company_name_3 in %s and contract='全部合约'"%(self.category,self.brokerNameParenth,self.brokerNameParenth),self.engine)
        elif self.data_source=='shanghai':
            position_data=pd.read_sql_query("select distinct * from gtja_intern.%s_volume_data where company_name_2 in %s "
                                            "or company_name_3 in %s and category='%s'"%(self.category,self.brokerNameParenth,self.brokerNameParenth,self.category),self.engine)
        #只取空头和多头仓位，不取前四列（总仓位）
        position_data=position_data.iloc[:,4:]
        position_data['update_date']=pd.to_datetime(position_data['update_date'])
        #将从sql中提取的数据中的空格去掉（sql中网页抓取的数字都是按照字符串型进行存储的，此处需要转换为浮点型）
        if self.data_source=='dalian':
            #去空格
            position_data['hold_vol_buy']=position_data['hold_vol_buy'].apply(lambda x:float(x.replace(',','')) if x!=u'\xa0' else np.nan)
            #去千分位符
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


        #读取活跃合约连续数据（也可换为wind商品指数）
        index_data=pd.read_csv("%sFI_1209.csv"%self.category.upper(),header=0,encoding='gbk')
        index_data['update_date']=pd.to_datetime(index_data['update_date'])
        index_data=index_data.sort('update_date')


        #计算换手数据（原本作为平仓条件使用，但是目前不使用该条件平仓）
        position_turn_over=index_data.loc[:,['update_date','volume','position_all']]
        position_turn_over['update_date']=pd.to_datetime(position_turn_over['update_date'])
        position_turn_over=position_turn_over.sort(['update_date'])
        position_turn_over['position_diff']=position_turn_over['position_all'].diff()
        position_turn_over['turn_over_rate']=position_turn_over['volume']/position_turn_over['position_diff']
        #换手率直接用绝对值进行比较，所以定义该函数。由于原始数据中存在空值和inf等异常值，所以需要进行一个逻辑判断
        def abs_(x):
            try:
                return np.abs(x)
            except:
                return np.nan
        position_turn_over['turn_over_rate']=position_turn_over['turn_over_rate'].apply(abs_)

        return position_data,index_data,position_turn_over

    @timeit
    def organize_data(self):
        position_data,index_data,position_turn_over=self.load_data()

        ####index_data####
        ##calculate moving average to find the trend
        index_data['MA5']=pd.rolling_mean(index_data['close'],30)
        index_data['MA10']=pd.rolling_mean(index_data['close'],60)


        #取差值作为趋势的等价
        index_data['trend']=index_data['MA5']-index_data['MA10']

        #由于开仓信号取决于仓位信号和趋势信号，所以为了避免未来函数，需要对这些开仓信号变量进行移动。
        #由于定为收盘时进行开仓和平仓操作，例子：2016/8/1日收盘后得到的趋势和仓位信号的原始日期标签是2016/8/1，
        #但是要等到2016/8/2收盘时才会运用到8/1收盘后的数据进行仓位的操作，所以8/1日的信号决定的收益是从2016/8/2日收盘
        #到2016/8/3日收盘之间的收益，在原始数据中，这个收益的日期标签是2016/8/3，所以需要对原始决策数据向后移动两天，
        #以在计算收益时能够对其对应的当日收益
        index_data=index_data.sort(['update_date'])
        for col in ['trend','MA5','MA10','position_all']:
            index_data[col]=index_data[col].shift(2)#原来是错位1
        #按照收盘价计算日对数收益率
        index_data['log_open']=np.log(index_data['close'])
        index_data['return_rate']=index_data['log_open'].diff()
        index_data=index_data.drop(['log_open'],axis=1)

        #为hmm模块预留的闭包函数，并未使用
        def hmm(category):
            def hmm_with_category(day):
                return execute(day,category)
            return hmm_with_category
        exe=hmm(self.category.upper())

        # # 为hmm模块预留的闭包函数，并未使用
        # index_data['trend']=map(exe,index_data['update_date'])
        # index_data['trend']=index_data['trend'].shift(1)

        ####position_data####
        #将原始数据中横向排列的多头和空头仓位数据重新纵向排列，对空头的仓位都乘以-1（空桶增仓的符号为-）
        def position_org(position_data):
            self.position_data_org=pd.DataFrame(columns=['company_name','position','position_chg','update_date','contract'])
            temp=position_data[['company_name_2','hold_vol_buy','hold_vol_buy_chg','update_date','contract']]
            temp=temp.rename(columns={'company_name_2':'company_name','hold_vol_buy':'position','hold_vol_buy_chg':'position_chg'})

            #给每个合约的持仓量变化方向贴上标签,方便之后判断当天是否是只开多(or只开空)
            temp['direction_tag']=temp['position_chg'].apply(lambda x: 'pos+' if x>0 else 'pos-')
            temp['tag']='pos'
            self.position_data_org=self.position_data_org.append(temp)
            temp=position_data[['company_name_3','hold_vol_sell','hold_vol_sell_chg','update_date','contract']]
            temp=temp.rename(columns={'company_name_3':'company_name','hold_vol_sell':'position','hold_vol_sell_chg':'position_chg'})
            temp['position']=-1*temp['position']
            temp['position_chg']=-1*temp['position_chg']

            #给每个合约的持仓量变化方向贴上标签,方便之后判断当天是否是只开多(or只开空)
            temp['direction_tag']=temp['position_chg'].apply(lambda x: 'neg+' if x<0 else 'neg-')
            temp['tag']='neg'
            self.position_data_org=self.position_data_org.append(temp)
            return self.position_data_org
        self.position_data_org=position_org(position_data)
        new_temp=[]
        for i,j in self.position_data_org.groupby(['update_date','company_name']):
            t=[i[0],i[1]]
            t.append(np.sum(j['position'].sum()))
            t.append(np.sum(j['position_chg'].sum()))
            l=pd.unique(j['direction_tag'])
            s=''
            for item in l:
                s=s+item
            t.append(s)
            new_temp.append(t)
        self.position_data_org_2=pd.DataFrame(new_temp,columns=['update_date','company_name','position','position_chg','direction_tag'])
        self.position_data_org_2['update_date']=pd.to_datetime(self.position_data_org_2['update_date'])
        # self.position_data_org_2=self.position_data_org.groupby(['update_date','company_name']).sum()
        #计算每日活跃合约总数
        try:
            self.position_data_org_2=self.position_data_org_2.drop(['contract'],axis=1)
            self.position_data_org_1=self.position_data_org.groupby(['update_date','company_name']).contract.count()
            self.position_data_org=pd.concat([self.position_data_org_2,self.position_data_org_1],axis=1,join='inner')
            self.position_data_org=self.position_data_org.loc[:,['position','position_chg','direction_tag','contract']]
        #如果失败则令每日的活跃合约总数为1
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


        #将全量日期对上筛选后的数据（因为无法保证特定交易商每天都出现在前二十大持仓中）
        self.position_data_selected=pd.merge(index_data[['update_date']],self.position_data_selected,on=['update_date'],how='left')
        ##将今天收盘得到的数据设定为后天的决策依据
        #理由同index_data中的错位
        self.position_data_lagged=pd.DataFrame()
        for i,j in self.position_data_selected.groupby('company_name'):
            j=j.sort('update_date')
            for col in ['position','position_chg','direction_tag']:
                j[col]=j[col].shift(2)##原来为1
            self.position_data_lagged=self.position_data_lagged.append(j)

        ####position_turn_over####
        #也要对换手率进行错位（若假定收盘才平仓）(最新版本中没有使用该条件)
        position_turn_over=position_turn_over.loc[:,['update_date','turn_over_rate']]
        position_turn_over['turn_over_rate']=position_turn_over['turn_over_rate'].shift(2)##原来为1
        return index_data,self.position_data_lagged,position_turn_over

    #用于计算是否符合仓位判断条件的函数。
    @timeit
    def position_rule(self,quantile_high,quantile_low):
        self.index_data,position_data,turn_over=self.organize_data()
        #index_data在index_rule中也会用到，所以将其作为对象的一个属性，方便之后直接使用，而不用重复计算
        index_data=self.index_data
        #将每天的总持仓量数据对上每家期货公司每天的持仓变化信息
        position_data=pd.merge(position_data,index_data[['update_date','position_all']],on=['update_date'],how='left')
        #将持仓变化除以总持仓，得到标准化之后的每日持仓变化
        position_data['position_chg']=position_data['position_chg']/position_data['position_all']
        position_data['position_chg']=position_data['position_chg'].fillna(0)



        t=pd.DataFrame()
        #滚动求每家的持仓量变化分位点阈值
        for i,j in position_data.groupby(['company_name']):
            j=j.sort(['update_date'])
            j['position_chg_high']=j['position_chg'].rolling(250).quantile(quantile_high)
            j['position_chg_low']=j['position_chg'].rolling(250).quantile(quantile_low)
            t=t.append(j)

        position_data=t

        #计算高于阈值和低于阈值的记录
        position_data['temp_high']=position_data['position_chg']-position_data['position_chg_high']
        position_data['temp_low']=position_data['position_chg']-position_data['position_chg_low']

        #将高于上侧阈值的记录记为1,其余标记为空
        position_data['temp_high']=position_data['temp_high'].apply(lambda x: 1 if x>0 else np.nan)
        #将低于下侧阈值的记录记为-1,其余标记为空
        position_data['temp_low']=position_data['temp_low'].apply(lambda x: -1 if x<0 else np.nan)
        position_data['position_signal']=position_data['temp_high']
        position_data['position_signal']=position_data['position_signal'].fillna(position_data['temp_low'])
        #计算持仓量变化的细节方向：
        #当总持仓变化增加极大时，同时需要满足以下条件：多头增加且空头未减少（即净仓位增加不是由空头减少、而是由多头增加带来的）
        def dir_tag(x):
            x=str(x)
            if x!='':

                #看多方向:多头多(tag为pos+),空头不减(空头减的tag为neg+)
                if x.find('pos+')!=-1 and x.find('neg-')==-1:
                    return 1
                #看空方向:多头不减(多头减的tag为pos-),空头减(tag为neg+)
                elif x.find('pos-')==-1 and x.find('neg+')!=-1:
                    return -1
            else:
                return np.nan
        position_data['temp_dir']=position_data['direction_tag'].apply(dir_tag)
        #如果净仓位变化大但是仓位方向不对，则仓位信号不为1或者-1
        # position_data['position_signal']=map(lambda x,y: x if x==y else np.nan,position_data['temp_dir'],position_data['position_signal'])
        position_data['position_signal']=(position_data['temp_dir']+position_data['position_signal'])/2
        def g(x):
            if x==1:
                return 1
            elif x==-1:
                return -1
            else:
                return np.nan
        position_data['position_signal']=position_data['position_signal'].apply(g)
        position_data=position_data.drop(['temp_high','temp_low','temp_dir'],axis=1)
        #给类对象一个attribute,名称为min_position_date,记录持仓量信号覆盖的时间区间的起点,可以用于之后作图部分。
        self.min_position_date=np.min(position_data['update_date'])
        #只返回含有日期、期货商名字、持仓量信号的三列
        return position_data[['update_date','company_name','position_signal']]

    #计算指数的趋势信号(ma30和ma60的差值)
    @timeit
    def index_data_rule(self):
        index_data=self.index_data
        def trend_dir(x):
            if x>0:
                return 1
            elif x<0:
                return -1
            else:
                return np.nan
        #确定趋势信号方向
        index_data['index_signal']=index_data['trend'].apply(trend_dir)
        #记录趋势信号开始时间,将其赋值给class的attribute
        self.min_index_date=np.min(index_data['update_date'])
        #值返回含有日期和趋势信号的dataframe
        return index_data[['update_date','index_signal']]


    #计算开始和结束条件
    @timeit
    def start_exit_signal(self):
        #持仓信号,上下限阈值分位点定为0.7和0.3
        p=self.position_rule(0.7,0.3)
        i=self.index_data_rule()
        #因为p中同一天数据会含有多条记录(不同期货交易商),所以要用outer方法进行表的列合并
        total=pd.merge(p,i,on=['update_date'],how='outer')
        #只有当趋势信号和持仓信号同时满足(同时为1或-1时),发出开仓信号,当同时为np.nan时,x==y的逻辑判断为False
        total['start_signal']=map(lambda x,y: x if x==y else np.nan,total['index_signal'],total['position_signal'])
        total_=pd.DataFrame()
        for i,j in total.groupby(['company_name']):
            col_list=list(j.columns)
            #取出三列分别在dataframe中对应的列号,方便之后将dataframe转换成矩阵之后使用numba jit和cython进行加速计算
            oi_index=col_list.index('position_signal')
            st_index=col_list.index('start_signal')
            tr_index=col_list.index('index_signal')
            t=j.as_matrix()
            if len(j)>0:
            #通过在类外定义的stop函数来输出平仓信号
                exit=stop(t,st_index,tr_index,oi_index)
                j['exit_signal']=exit
                j=j.sort(['update_date'])
                #将开仓和平仓信号存储到trade_signal列中
                j['trade_signal']=j['start_signal'].fillna(j['exit_signal'])
                j['trade_signal']=j['trade_signal'].fillna(method='ffill')
                total_=total_.append(j)
            else:
                pass

        return total_[['company_name','update_date','trade_signal']]

    #止损函数(详见stop_loss.pyx文件)
    @timeit
    def stop_loss(self,trade_signal,close_high,close_low,return_rate,threshold=-0.04):
        return stop_loss.stop_loss(trade_signal,close_high,close_low,return_rate,threshold)

    #找出每一个单笔交易的函数
    @timeit
    def sep_trade(self,trade_signal):
        return sep_trade(trade_signal)

    #找出单笔交易的函数
    @timeit
    def sep_trades(self):
        trade_signal=self.start_exit_signal()
        index_data=self.index_data
        #计算每日最高(低)价与收盘价之间的差幅(用于日内止损)
        index_data['high_close']=np.log(index_data['close'])-np.log(index_data['high'])
        index_data['low_close']=np.log(index_data['low'])-np.log(index_data['close'])

        index_data=index_data[['update_date','return_rate','high_close','low_close']]

        trade_signal=pd.merge(index_data,trade_signal,on=['update_date'],how='inner')
        ts_=pd.DataFrame()
        for i,j in trade_signal.groupby(['company_name']):
            j=j.sort(['update_date'])
            ts=np.array(j['trade_signal'])
            tn=self.sep_trade(ts)
            j['trade_num']=tn
            ts_=ts_.append(j)
        return ts_

    @timeit
    def stop_loss_trades(self):
        df=self.sep_trades()
        df=df[np.isnan(df['trade_num'])==False]
        new_df=pd.DataFrame()
        #把数据按照期货商和单次交易代号进行分组(找到某家期货商某次交易)
        for i,j in df.groupby(['company_name','trade_num']):
            j=j.sort(['update_date'])
            #构造数组用于之后的函数
            trade_signal=np.array(j['trade_signal'])
            return_rate=np.array(j['return_rate'])
            high_close=np.array(j['high_close'])
            low_close=np.array(j['low_close'])
            #进行if判断,防止数据集中所有的交易信号均为nan(即无交易信号)
            if np.sum(np.isnan(trade_signal)) != len(trade_signal):
                tr, r=self.stop_loss(trade_signal, high_close, low_close, return_rate, threshold=-0.04)
                temp=pd.DataFrame()
                temp['update_date']=j['update_date']
                temp['trade_signal']=tr
                temp['daily_return']=r
                temp['company_name']=i[0]
                new_df=new_df.append(temp)
            else:
                pass
        new_df_=pd.DataFrame()
        if len(new_df)>0:
            for i,j in new_df.groupby(['company_name']):
                #再次对上全部交易日期
                j=pd.merge(j,self.index_data[['update_date']],on=['update_date'],how='outer')
                j=j.sort(['update_date'])
                #将没有交易信号(包括既没有开多,也不开空,也不平仓的日期)的当日收益(即为nan)填充0
                j['daily_return']=j['daily_return'].fillna(0)
                #将为空的交易信号填充0值(即仓位为0)
                j['trade_signal']=j['trade_signal'].fillna(0)
                #将公司名赋值
                j['company_name']=i
                new_df_=new_df_.append(j)
        else:
            pass
        new_df=new_df_
        return new_df

    #画图
    @timeit
    def plot_fig(self):
        df=self.stop_loss_trades()
        df['update_date']=pd.to_datetime(df['update_date'])
        total_df=pd.DataFrame()
        total_df['update_date']=pd.unique(df['update_date'])
        total_df.index=[total_df['update_date']]

        total_df['daily_return']=list(df.groupby(['update_date']).daily_return.mean())
        total_df['trade_signal']=list(df.groupby(['update_date']).trade_signal.mean())

        total_df=total_df[np.max((self.min_position_date,self.min_index_date)):]
        total_df['cum_return']=total_df['daily_return'].cumsum()

        total_df['max_return']=total_df['cum_return'].cummax()
        total_df['drawdown']=total_df['max_return']-total_df['cum_return']
        total_df['updaet_date']=pd.to_datetime(total_df['update_date'])
        total_df=total_df[pd.to_datetime('2014-01-01'):pd.to_datetime('2015-01-01')]

        price=self.index_data
        # price=price[price['update_date']>=np.max((self.min_position_date,self.min_index_date))]
        price=price[price['update_date']>=pd.to_datetime('2014-01-01')]
        price=price[price['update_date']<=pd.to_datetime('2015-01-01')]

        position=self.position_rule(0.7,0.3)
        position=pd.DataFrame(position.groupby(['update_date']).position_signal.sum())
        position.reset_index(inplace=True)
        position['update_date']=pd.to_datetime(position['update_date'])
        position.index=[position['update_date']]
        position=position[position['update_date']>=pd.to_datetime('2014-01-01')]
        position=position[position['update_date']<=pd.to_datetime('2015-01-01')]


        import matplotlib.pyplot as plt
        plt.figure(figsize=(15,10))
        ax1=plt.subplot(1,1,1)
        ax1.plot(total_df.index,total_df['cum_return'],'g.-')
        ax2=ax1.twinx()
        ax2.plot(price['update_date'],price['close'],'ro-')
        ax2.plot(price['update_date'],price['MA5'])
        ax2.plot(price['update_date'],price['MA10'])
        ax1.bar(total_df.index,total_df['trade_signal'])
        ax1.bar(position.index,position['position_signal'],color='yellow')

        plt.show()


if __name__=='__main__':
    p={'category':'zn','ex':'shanghai'}
    engine = create_engine("mysql+pymysql://liyuefan:1994050306@localhost/gtja_intern?charset=utf8")
    asset_1=gtja_commodity([u'浙商期货',u'永安期货'],engine,p['category'],p['ex'])
    pinyin={u'永安期货':'yongan',u'浙商期货':'zheshang'}
    st=time.time()
    raw=asset_1.plot_fig()
    ed=time.time()
    print 'total time: ',ed-st