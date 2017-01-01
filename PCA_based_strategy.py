#! /Users/liyuefan/anaconda2/bin/python
#  coding: utf-8


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import calendar



data=pd.read_csv('/Users/liyuefan/Documents/gtja/GSCI_ER_Indices.csv',header=None)

index_list=data.iloc[0,:].dropna()
index_list=map(lambda x: x.split(' ')[0],index_list)

ER_dict={'SPGCCCP':'Cocoa','SPGCCNP':'Corn','SPGCCTP':'Cotton','SPGCKCP':'Coffee',
        'SPGCSBP':'Sugar','SPGCKWP':'Kansas wheat','SPGCWHP':'Wheat',
         'SPGCSOP':'Soybeans','SPGCLCP':'Live cattle','SPGCLHP':'Lean hogs','SPGCFCP':'Feeder cattle',
        'SPGCIAP':'Aluminium','SPGCICP':'Copper','SPGCIKP':'Nickel','SPGCILP':'Lead','SPGCIZP':'Zinc',
        'SPGCBRP':'Brent','SPGCCLP':'Crude oil','SPGCGOP':'Gasoil','SPGCHOP':'Heating oil',
        'SPGCHUP':'Gasoline','SPGCNGP':'Natural Gas','SPGCGCP':'Gold','SPGCSIP':'Silver'}
def name_kind(x):
    return ER_dict[x]


def plot_loading(r_all):
    for i in range(r_all.shape[1]):
        plt.figure(figsize=(3,9))
        plt.subplot(r_all.shape[1],1,i+1)

        temp=r_all[[r_all.columns[i]]].sort(r_all.columns[i])
        xticks=np.arange(len(temp))
        xlabels=list(temp.index)
        plt.barh(xticks,temp[r_all.columns[i]],align='center',color='yellow',alpha=0.8)
        plt.title('loadings of PC%s'%(i+1))
        plt.yticks(xticks,xlabels,size='medium',rotation=0);
        plt.autoscale()



data_for_PCA=pd.DataFrame()
for i in range(data.shape[1]):
    if i%3==1:
        temp=data.iloc[2:,[i-1,i]]
        temp=temp.rename(columns={i-1:'update_date',i:'%s'%index_list[i/3]})
        temp['update_date']=pd.to_datetime(temp['update_date'])
        temp.index=[temp['update_date']]
        temp=temp.drop(['update_date'],axis=1)
        data_for_PCA=pd.concat([data_for_PCA,temp],axis=1,join='inner')
    else:
        pass

y=data_for_PCA['SPGSCI'].apply(float)
ind_var=data_for_PCA.copy()
ind_var_diff=pd.DataFrame()
for col in ind_var.columns:
    ind_var[col]=ind_var[col].apply(float)
    ind_var_diff[col]=np.diff(np.log(ind_var[col]))
ind_var_diff['update_date']=ind_var.index[1:]
ind_var_diff.index=[ind_var_diff['update_date']]
y=ind_var_diff[['SPGSCI']]
ind_var_diff.drop(['update_date','SPGSCI'],axis=1,inplace=True)


from sklearn.decomposition import PCA as PCA
from sklearn.linear_model import LinearRegression



def pca_weight(ind_var_diff):
    X=ind_var_diff.as_matrix()

    pca=PCA(n_components=10,whiten=True)

    pca.fit(X)

    X=pca.transform(X)

    r=pd.DataFrame(pca.components_[0])
    r['name']=map(name_kind,ind_var_diff.columns)
    r.index=[r['name']]

    r.drop('name',axis=1,inplace=True)

    weights=r[0]

    weights=weights/sum(weights)
    return list(weights),pca


##输入的参数all_data需要时间戳格式的索引(index)列
def loop_pca(all_data):
    total=[]
    pca_all=[]
    date_start=pd.to_datetime(min(all_data.index))
    date_start=date_start+np.timedelta64(2,'Y')+np.timedelta64(7,'D')
    date_end=pd.to_datetime(max(all_data.index))
    for day in pd.date_range(date_start,date_end):
        if calendar.weekday(day.year,day.month,day.day)==1:
            day_=day-np.timedelta64(7,'D')
            date_f=day_-np.timedelta64(2,'Y')
            date_t=day_
            date_t=date_t-np.timedelta64(1,'D')

            ind_var_diff=all_data[date_f:date_t]
            w,pca=pca_weight(ind_var_diff)
            pca_all.append(pca)
            w.append(day)
            total.append(w)
        else:
            w=[np.nan for x in np.arange(all_data.shape[1])]
            w.append(day)
            total.append(w)
    col_list=list(all_data.columns)
    col_list.append('update_date')
    all_w=pd.DataFrame(total,columns=col_list)
    all_w['update_date']=pd.to_datetime(all_w['update_date'])
    all_w=all_w.fillna(method='ffill')
    all_w=all_w.dropna(axis=0)
    return all_w,pca_all


st=datetime.datetime.now()
all_w,pca_all=loop_pca(ind_var_diff)
ed=datetime.datetime.now()
print ed-st


all_w['update_date']=all_w['update_date'].apply(lambda x:pd.to_datetime(x.date()))
all_w.index=[all_w['update_date']]
all_w.drop('update_date',axis=1,inplace=True)

return_mat=ind_var_diff
return_mat['temp']=1
all_w=pd.concat([all_w,return_mat[['temp']]],axis=1,join='inner')
all_w.drop('temp',axis=1,inplace=True)
return_mat.drop('temp',axis=1,inplace=True)

return_mat=ind_var_diff[np.min(all_w.index):np.max(all_w.index)]


all_w_mat=all_w.as_matrix()
return_mat_mat=return_mat.as_matrix()

cal_mat=np.dot(return_mat_mat,all_w_mat.T)

return_series=cal_mat.diagonal()
return_series_avg=pd.DataFrame(return_mat.mean(axis=1))



f=pd.DataFrame()
f['update_date']=all_w.index
f['beta_return']=return_series
f.index=[f['update_date']]
f.drop('update_date',axis=1,inplace=True)
f=pd.concat([f,y],axis=1,join='inner')
f=pd.concat([f,return_series_avg],axis=1,join='inner')
f=f.rename(columns={0:'avg_return'})


f['cum_beta']=f['beta_return'].cumsum()
f['cum_gsci']=f['SPGSCI'].cumsum()
f['cum_avg']=f['avg_return'].cumsum()

plt.figure(figsize=(20,10))
plt.plot(f['cum_beta'],label='beta')
plt.plot(f['cum_avg'],label='avg')
plt.plot(f['cum_gsci'],label='gsci')
plt.legend()
plt.show()



plt.figure(figsize=(15,5))
plt.plot(f['cum_beta']-f['cum_gsci'])
plt.show()


f['strategy_return']=f['beta_return']-f['SPGSCI']
f['cum_strategy']=f['strategy_return'].cumsum()
f['max_cum']=f['cum_strategy'].cummax()
f['draw_down']=f['max_cum']-f['cum_strategy']

print 'Cumulative Return:\t',f['cum_strategy'][-1]

print 'Max Drawdown:\t',f['draw_down'].max()

f['strategy_return']=f['beta_return']-f['SPGSCI']

print 'Sharpe Ratio:\t',((f['cum_beta']-f['cum_gsci'])[-1]/12-0.03)/(np.std(f['beta_return']-f['SPGSCI'])*np.sqrt(250))

plt.figure(figsize=(30,60))
for i in range(len(all_w.columns)):

    plt.subplot(len(all_w.columns),1,i+1)
    plt.plot(all_w[all_w.columns[i]],label=ER_dict[all_w.columns[i]],lw=4)

    plt.title(ER_dict[all_w.columns[i]])
    plt.autoscale()













