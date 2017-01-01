#! /Users/liyuefan/anaconda2/bin/python
#  coding: utf-8


from hmmlearn.hmm import GMMHMM,GaussianHMM
import pandas as pd
import numpy as np
import seaborn as sns
import warnings
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')


data=pd.read_csv('/Users/liyuefan/Documents/gtja/IFI.csv',header=0,encoding='gbk')
data['update_date']=pd.to_datetime(data['update_date'])
new_data=pd.DataFrame()
for col in data.columns:
    if col=='update_date':
        new_data[col]=data[col][1:]
    else:
        new_data[col]=data[col][:-1]
data=new_data

train_data=data[data['update_date']<=pd.to_datetime('2016-06-30')]
train_data=train_data[train_data['update_date']>=pd.to_datetime('2014-06-30')]
test_data=data[data['update_date']>=pd.to_datetime('2016-07-01')]
test_data=test_data[test_data['update_date']<=pd.to_datetime('2016-10-01')]

r_5=np.array(np.log(train_data['close'][5:]))-np.array(np.log(train_data['close'][:-5]))
r_1=(np.array(np.log(train_data['close'][1:]))-np.array(np.log(train_data['close'][:-1])))[4:]
r_range=(np.array(np.log(train_data['high']))-np.array(np.log(train_data['low'])))[5:]

date_list=train_data['update_date'][5:]


r_5_test=np.array(np.log(test_data['close'][5:]))-np.array(np.log(test_data['close'][:-5]))
r_1_test=(np.array(np.log(test_data['close'][1:]))-np.array(np.log(test_data['close'][:-1])))[4:]
r_range_test=(np.array(np.log(test_data['high']))-np.array(np.log(test_data['low'])))[5:]
date_list_test=test_data['update_date'][5:]

X=np.column_stack([r_1,r_5,r_range])

X_test=np.column_stack([r_1_test,r_5_test,r_range_test])


hmm = GaussianHMM(n_components = 13, covariance_type='diag',n_iter = 5000).fit(X)
latent_states_sequence_train = hmm.predict(X)
len(latent_states_sequence_train)



sns.set_style('white')

mean_return_dict={}
plt.figure(figsize = (15, 8))
for i in range(hmm.n_components):
    state = (latent_states_sequence_train == i)
    plt.plot(date_list[state],train_data['close'][state],'o',label = 'latent state %d'%i,lw = 1)
    plt.legend()
    plt.grid(1)
    mean_return_dict[i]=np.mean(r_1[state])
plt.plot()



latent_states_sequence_test = hmm.predict(X_test)

first_5_predict=latent_states_sequence_test



pair=mean_return_dict.items()
pair=filter(lambda x: False if np.isnan(x[1]) else True,pair)
pair_sorted=sorted(pair, key=lambda x: x[1])
high_threshold=pair_sorted[-4][1]
low_threshold=pair_sorted[3][1]

def compare(x):
    if x>high_threshold:
        return 1
    elif x<low_threshold:
        return -1
    else:
        return np.nan


expected_return_series=map(lambda x:mean_return_dict[x],latent_states_sequence_test)
expected_return_series=np.array(map(compare,expected_return_series[:-1]))
print expected_return_series
real_return_series=r_1_test[1:]
real_return_series=np.array(map(lambda x:1 if x>0 else -1, real_return_series))

temp = expected_return_series-real_return_series
temp=filter(lambda x:True if np.isnan(x)==False else False,temp)
print (len(temp)-np.sum(np.abs(temp))/2.)/len(temp)
real_return_series=list(real_return_series)
print real_return_series.count(1)/float(len(real_return_series))
print real_return_series.count(-1)/float(len(real_return_series))





sns.set_style('white')
plt.figure(figsize = (15, 8))
for i in range(hmm.n_components):
    state = (latent_states_sequence_test == i)
    plt.plot(date_list_test[state],test_data['close'][state],'o',label = 'latent state %d'%i,lw = 1)
    plt.legend()
    plt.grid(1)
plt.plot()
