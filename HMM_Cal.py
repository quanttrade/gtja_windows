#! /Users/liyuefan/anaconda2/bin/python
#  coding: utf-8

import pandas as pd
import numpy as np
import warnings
import datetime
from hmmlearn.hmm import GaussianHMM
import copy
import calendar
warnings.filterwarnings('ignore')


def read_data(csv, file_path=None):
    if csv == 1 and file_path is None:
        raise Exception('Wrong parameter')
    elif csv == 1 and file_path is not None:
        data = pd.read_csv(file_path)
        return data
    elif csv == 0 and file_path is None:

        ##通过wind接口读取
        from WindPy import w

        w.start()

        data=w.wsd("I.DCE", "open,high,low,close,volume,amt", "2000-11-02", str(datetime.date.today()), "")

        df=pd.DataFrame()
        df['update_date']=data.Times
        for i in range(len(data.Fields)):
            df[data.Fields[i]]=data.Data[i]
            df[data.Fields[i]]=df[data.Fields[i]].apply(float)
        df['update_date']=pd.to_datetime(df['update_date'])
        df['update_date']=df['update_date'].apply(lambda x:x.date())


        w.close()
        return df
    elif csv == 0 and file_path is not None:
        ##也通过wind接口读取
        from WindPy import w

        w.start()

        data=w.wsd("I.DCE", "open,high,low,close,volume,amt", "2000-11-02", str(datetime.date.today()), "")

        df=pd.DataFrame()
        df['update_date']=data.Times
        for i in range(len(data.Fields)):
            df[data.Fields[i]]=data.Data[i]
            df[data.Fields[i]]=df[data.Fields[i]].apply(float)
        df['update_date']=pd.to_datetime(df['update_date'])
        df['update_date']=df['update_date'].apply(lambda x:x.date())


        w.close()
        return df



def data_cleanse(csv,file_path):
    df = read_data(csv,file_path)
    if 'update_date' in df.columns:
        df['update_date'] = pd.to_datetime(df['update_date'])
    else:
        raise Exception('The data have no date column')
    ##将时间和其他维度进行错位
    data_lag=pd.DataFrame()
    for col in df.columns:
        if col == 'update_date':
            time=list(df[col][1:])
            time.append(np.max(time)+np.timedelta64(1,'D'))
            data_lag[col]=time
        else:
            data_lag[col]=df[col]
    col_without_date=list(data_lag.columns)
    col_without_date.remove('update_date')
    for col in col_without_date:
        data_lag[col]=data_lag[col].apply(float)
    return data_lag,df

def train_test(day,data):
    day=pd.to_datetime(day)
    train_period_start=day-np.timedelta64(1,'D')-np.timedelta64(2,'Y')
    train_period_end=day-np.timedelta64(1,'D')
    test_period_start=day
    test_period_end_temp=day+np.timedelta64(3,'M')
    test_period_end=np.min((pd.to_datetime(np.max(data['update_date'])),test_period_end_temp))
    return train_period_start, train_period_end, test_period_start, test_period_end

def hmm_weight(df,data_raw,day,n_components,plot=False):

    tr_start,tr_end,te_start,te_end=train_test(day,df)
    col_list=['update_date','open','high','low','close']
    df=df.loc[:,col_list]
    df=df.dropna(axis=0)
    data_raw=data_raw.loc[:,col_list]
    data_raw=data_raw.dropna(axis=0)

    train_df=df.loc[df['update_date']>=tr_start,:].loc[df['update_date']<=tr_end,:]
    test_df=df.loc[df['update_date']>=te_start,:].loc[df['update_date']<=te_end,:]

    train_close=data_raw.loc[data_raw['update_date']>=tr_start,:].loc[data_raw['update_date']<=tr_end,:]
    test_close=data_raw.loc[data_raw['update_date']>=te_start,:].loc[data_raw['update_date']<=te_end,:]

    if len(train_df)>0 and len(test_df)>0:
        r_5 = np.array(np.array(np.log(train_df['close'][5:])) - np.array(np.log(train_df['close'][:-5])))[:]
        # r_10 = np.array(np.array(np.log(train_df['close'][10:])) - np.array(np.log(train_df['close'][:-10])))

        r_1 = np.array(np.array(np.log(train_df['close'][1:])) - np.array(np.log(train_df['close'][:-1])))[4:]


        r_range = np.array((np.array(np.log(train_df['high']))
                   - np.array(np.log(train_df['low']))))[5:]

        r_1 = np.array(map(lambda x: 0 if x==np.inf or x==-np.inf or np.isnan(x) else x, r_1))
        r_5 = np.array(map(lambda x: 0 if x==np.inf or x==-np.inf or np.isnan(x) else x, r_5))
        # r_10 = np.array(map(lambda x: 0 if x==np.inf or x==-np.inf or np.isnan(x) else x, r_10))
        r_range = np.array(map(lambda x: 0 if x==np.inf or x==-np.inf or np.isnan(x) else x, r_range))


        r_1_no_lag=list(r_1[1:])
        r_1_no_lag.append(0)
        r_1_no_lag=np.array(r_1_no_lag)


        date_list = train_df['update_date'][5:]

        r_5_test = np.array(np.array(np.log(test_df['close'][5:])) - np.array(np.log(test_df['close'][:-5])))[:]
        # r_10_test = np.array(np.array(np.log(test_df['close'][10:])) - np.array(np.log(test_df['close'][:-10])))
        r_1_test = np.array(np.array(np.log(test_df['close'][1:]))- np.array(np.log(test_df['close'][:-1])))[4:]
        r_1_test = np.array(map(lambda x: 0 if x==np.inf or x==-np.inf or np.isnan(x) else x, r_1_test))
        r_5_test = np.array(map(lambda x: 0 if x==np.inf or x==-np.inf or np.isnan(x) else x, r_5_test))
        # r_10_test = np.array(map(lambda x: 0 if x==np.inf or x==-np.inf or np.isnan(x) else x, r_10_test))

        r_1_test_no_lag=list(r_1_test[1:])
        r_1_test_no_lag.append(0)
        r_1_test_no_lag=np.array(r_1_test_no_lag)

        r_range_test = np.array(np.array(np.log(test_df['high'])) - np.array(np.log(test_df['low'])))[5:]
        r_range_test = np.array(map(lambda x: 0 if x==np.inf or x==-np.inf or np.isnan(x) else x, r_range_test))

        date_list_test = test_df['update_date'][5:]

        X = np.column_stack([r_1, r_5, r_range])

        X_test = np.column_stack([r_1_test, r_5_test, r_range_test])
        if X.shape[0]>=n_components and X_test.shape[0]>=n_components:

            hmm = GaussianHMM(n_components=n_components, covariance_type='diag', n_iter=2000).fit(X)
            latent_states_sequence_train = hmm.predict(X)



            mean_return_dict = {}
            if plot==True:
                import matplotlib.pyplot as plt
                import seaborn as sns
                sns.set_style('white')
                plt.figure(figsize=(15, 8))



                for i in range(hmm.n_components):
                    state = (latent_states_sequence_train == i)
                    sharpe=(np.mean(r_1_no_lag[state])*252-0.03)/(np.std(r_1_no_lag[state])*np.sqrt(252))
                    plt.plot(date_list[state], train_close['close'][state], 'o', label='latent state %d: %s' % (i,sharpe), lw=5)
                    plt.legend()
                    plt.grid(1)
                    mean_return_dict[i] = sharpe

                plt.show()
            else:
                for i in range(hmm.n_components):
                    state = (latent_states_sequence_train == i)
                    mean_return_dict[i] = (np.mean(r_1_no_lag[state])*252-0.03)/(np.std(r_1_no_lag[state])*np.sqrt(252))

            latent_states_sequence_test = hmm.predict(X_test)



            pair = mean_return_dict.items()
            pair = filter(lambda x: False if np.isnan(x[1]) else True, pair)
            pair_sorted = sorted(pair, key=lambda x: x[1])
            highest = pair_sorted[-1]
            lowest = pair_sorted[0]
            # print pair_sorted



            expected_return_series = map(lambda x: mean_return_dict[x], latent_states_sequence_test)
            expected_return_series = np.array(map(lambda x: 1 if x > 0 else -1, expected_return_series[:-1]))
            real_return_series = r_1_test[1:]
            real_return_series = np.array(map(lambda x: 1 if x > 0 else -1, real_return_series))

            temp = expected_return_series - real_return_series
            temp = filter(lambda x: True if np.isnan(x) == False else False, temp)
            # acc_rate=(len(temp) - np.sum(np.abs(temp)) / 2.) / len(temp)
            # print acc_rate
            real_return_series = list(real_return_series)
            # print real_return_series.count(1) / float(len(real_return_series))
            # print real_return_series.count(-1) / float(len(real_return_series))
            # print 'time: ',np.max(date_list_test),'expected Sharpe: ',mean_return_dict[latent_states_sequence_test[-1]]


            prediction=pd.DataFrame()
            prediction['update_date']=date_list_test
            prediction['state']=latent_states_sequence_test
            prediction['expected_sharpe']=prediction['state'].apply(lambda x:mean_return_dict[x])


            if plot==True:
                sns.set_style('white')
                plt.figure(figsize=(8, 4))
                for i in range(hmm.n_components):
                    state = (latent_states_sequence_test == i)
                    plt.plot(date_list_test[state], test_close['close'][state], 'o', label='latent state %d: %s' % (i,mean_return_dict[i]), lw=5)
                    plt.grid(1)
                    plt.legend()

                plt.show()
            else:
                pass
            if plot==True:
                sns.set_style('white')
                plt.figure(figsize=(15,10))
                # plt.subplot(2,1,1)
                new_frame=copy.deepcopy(prediction)
                new_frame.index=[new_frame['update_date']]
                new_frame['expected_return']=new_frame['expected_sharpe'].apply(lambda x: 30 if x>0 else -30)
                test_close.index=[test_close['update_date']]
                test_close['close']=test_close['close']-420
                test_close=test_close[np.min(new_frame['update_date']):np.max(new_frame['update_date'])]
                plt.plot(test_close['close'],'o-',color='red')
                # plt.subplot(2,1,2)
                plt.bar(new_frame.index,new_frame['expected_return'],align='edge',alpha=0.5,color='yellow')
                plt.show()

            return prediction, highest, lowest
        else:
            return None,None,None
    else:
        return None,None,None

def execute(day,category):
    day=pd.to_datetime(day)
    day_sep=day-np.timedelta64(2,'M')
    df,data_raw=data_cleanse(1,'/Users/liyuefan/Documents/gtja/%sFI_1209.csv'%category)
    try:

        prediction,highest,lowest=hmm_weight(df,data_raw,day_sep,3,plot=False)
        if prediction is not None:
            prediction=prediction[prediction['update_date']==day]

            ##################################################################
            if prediction['state'].values[0]==highest[0] or prediction['state'].values[0]==lowest[0]:
                print 'time: ',day,'expected Sharpe: ',prediction['expected_sharpe'].values[0],calendar.weekday(day.year,day.month,day.day)
                return prediction['expected_sharpe'].values[0]

            else:
                print 'time: ',day,'expected Sharpe: ',np.nan,calendar.weekday(day.year,day.month,day.day)
                return np.nan
            ##################################################################
            print 'time: ',prediction['update_date'].values[0],'expected Sharpe: ',prediction['expected_sharpe'].values[0]
            return prediction['expected_sharpe'].values[0]
        else:
            return np.nan
    except:
        print 'time: ',day,'fail',calendar.weekday(day.year,day.month,day.day)
        return np.nan


def adaboost_execute(day):
    day_l=[day for i in range(10)]
    l=map(execute,day_l)
    l=map(lambda x: 0 if np.isnan(x) else x, l)
    print day, np.mean(l)
    return np.mean(l)


if __name__=='__main__':
    st=datetime.datetime.now()
    expected_sharpe=execute('2016-12-22','zn')
    ed=datetime.datetime.now()
    print ed-st
