import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm

##interday data
p_df_inter=pd.read_csv('/Users/liyuefan/Documents/gtja/CUFI_zhulian.csv',encoding='gbk')
p_df_inter['update_date']=pd.to_datetime(p_df_inter['update_date'])
p_df_inter.index=[p_df_inter['update_date']]
p_df_inter=p_df_inter.drop(['update_date'],axis=1)


#intraday data
p_df_intra=pd.read_csv('/Users/liyuefan/Documents/gtja/CU_intraday_2year.csv',encoding='gbk')
p_df_intra['update_date']=pd.to_datetime(p_df_intra['update_date'])
p_df_intra['date']=p_df_intra['update_date'].apply(lambda x:x.date())
# select the certain minute in a day for trading.
p_df_intra_=pd.DataFrame()
for i,j in p_df_intra.groupby(['date']):
    j=j.sort(['update_date'])
    t=j.iloc[5:]
    p_df_intra_=p_df_intra_.append(t)
p_df_intra_['date']=pd.to_datetime(p_df_intra_['date'])
p_df_intra=p_df_intra_
p_df_intra.index=[p_df_intra['date']]
p_df_intra=p_df_intra.drop(['update_date','date'],axis=1)
p_df_intra=p_df_intra[['close']]
p_df_intra=p_df_intra.rename(columns={'close':'open'})

p_df=pd.concat([p_df_inter[['high','low','close']],p_df_intra[['open']]],axis=1,join='inner')


#LME data
lme_df = pd.read_excel('/Users/liyuefan/Documents/gtja/LME_COPPER.xlsx', sheetname='Sheet1')
N_col = lme_df.shape[1]
update_date = lme_df.iloc[3:, 0]
lme_df_ = pd.DataFrame()
lme_df_['update_date'] = update_date
for i in range(1, N_col, 2):
    indicator_name = lme_df.iloc[1, i]
    data = lme_df.iloc[30:, i]
    lme_df_[indicator_name] = data

lme_df = lme_df_
lme_df['update_date'] = pd.to_datetime(lme_df['update_date'])
lme_df.index = [lme_df['update_date']]
lme_df = lme_df.drop(['update_date'], axis=1)
lme_df = lme_df.apply(lambda x: x.astype(float), axis=1)


# lme_df['NON-COMMERCIAL LONG PERCENTAGE']=lme_df['NON-COMMERCIAL LONG']/lme_df['OPEN INTEREST']
# lme_df['NON-COMMERCIAL SHORT PERCENTAGE']=lme_df['NON-COMMERCIAL SHORT']/lme_df['OPEN INTEREST']
# lme_df['COMMERCIAL SHORT PERCENTAGE']=lme_df['COMMERCIAL SHORT']/lme_df['OPEN INTEREST']
# lme_df['COMMERCIAL LONG PERCENTAGE']=lme_df['COMMERCIAL LONG']/lme_df['OPEN INTEREST']
# lme_df['NET NON-COMMERCIAL PERCENTAGE']=lme_df['NON-COMMERCIAL LONG PERCENTAGE']-lme_df['NON-COMMERCIAL SHORT PERCENTAGE']

#THIS IS THE X IN REGRESSION
lme_df['NET_COMM_PER']=(lme_df['NON-COMMERCIAL LONG']-lme_df['NON-COMMERCIAL SHORT'])/lme_df['OPEN INTEREST']


#CFTC data
cftc=pd.read_csv('/Users/liyuefan/Documents/gtja/CFTC_CU.csv',encoding='gbk',thousands=',')

cftc_data=cftc.iloc[1:,:]
cftc_cln=pd.DataFrame(cftc_data)
cftc_cln.columns=['update_date','non_comm_long','non_comm_short','non_comm_arb','comm_long','comm_short','open_interest']
cftc_cln=cftc_cln.dropna(axis=0)
cftc_cln['update_date']=pd.to_datetime(cftc_cln['update_date'])


def thousands(series):
    return series.str.replace(',','').astype(float)

for col in cftc_cln.columns:
    if col!='update_date':
        cftc_cln[col]=thousands(cftc_cln[col])
    else:
        pass

cftc_cln['non_comm_net']=cftc_cln['non_comm_long']-cftc_cln['non_comm_short']
#THIS IS THE Y IN REGRESSION
cftc_cln['non_comm_per']=cftc_cln['non_comm_net']/cftc_cln['open_interest']
cftc_cln.index=[cftc_cln['update_date']]
cftc_cln=cftc_cln.drop(['update_date'],axis=1)


regr_df=pd.concat([lme_df[['NET_COMM_PER']],cftc_cln[['non_comm_per']]],axis=1,join='inner')

regr_df=regr_df.dropna(axis=0)

update_date=list(regr_df.index)

X=np.array(regr_df['NET_COMM_PER'])
X=sm.add_constant(X)
Y=np.array(regr_df['non_comm_per'])

#rolling linear regression

def rolling_lm(Y,X,step):
    if len(Y)==len(X):
        N=len(Y)
        full_cftc_array=np.zeros((N,2),dtype=np.float)
        full_cftc_array[:,:]=np.nan
        for i in range(step-1,N):
            X_train=X[np.max((0,i-step+1)):i]
            Y_train=Y[np.max((0,i-step+1)):i]
            lm=sm.OLS(Y_train,X_train)
            result=lm.fit()
            param=result.params
            full_cftc_array[i,0]=param[0]
            full_cftc_array[i,1]=param[1]
    else:
        return None
    return full_cftc_array

Y_param=rolling_lm(Y,X,30)

#regr_param is used to store regression result
regr_param=pd.DataFrame()
regr_param['update_date']=update_date
regr_param['const']=Y_param[:,0]
regr_param['coef']=Y_param[:,1]
regr_param.index=[regr_param['update_date']]
regr_param=regr_param.drop(['update_date'],axis=1)

lme_df=pd.concat([lme_df,regr_param],axis=1,join='outer')

lme_df['const']=lme_df['const'].shift(4)
lme_df['coef']=lme_df['coef'].shift(4)
lme_df['const']=lme_df['const'].fillna(method='ffill')
lme_df['coef']=lme_df['coef'].fillna(method='ffill')

lme_df['cftc']=lme_df['coef']*lme_df['NET_COMM_PER']+lme_df['const']
lme_df=lme_df.dropna(axis=0)

full_df=lme_df[['cftc']]
full_df=pd.concat([full_df,p_df[['open','close']]],axis=1,join='inner')

full_df['r']=np.log(full_df['close'])
full_df['r']=full_df['r'].diff()

# full_df['r']=(full_df['close']-full_df['open'])/full_df['open']
#
# full_df['r']=np.log(full_df['open'])
# full_df['r']=full_df['r'].diff()


full_df['c_ma']=pd.rolling_mean(full_df['close'],5)
full_df['o_ma']=pd.rolling_mean(full_df['open'],5)
full_df['cftc_ma']=pd.rolling_mean(full_df['cftc'],5)

full_df['c_ma_diff']=full_df['c_ma'].diff()
full_df['o_ma_diff']=full_df['o_ma'].diff()
full_df['cftc_ma_diff']=full_df['cftc_ma'].diff()



full_df['c_up_thr']=pd.rolling_quantile(full_df['c_ma_diff'],100,0.6)
full_df['c_low_thr']=pd.rolling_quantile(full_df['c_ma_diff'],100,0.4)
full_df['o_up_thr']=pd.rolling_quantile(full_df['o_ma_diff'],100,0.6)
full_df['o_low_thr']=pd.rolling_quantile(full_df['o_ma_diff'],100,0.4)
full_df['cftc_up_thr']=pd.rolling_quantile(full_df['cftc_ma_diff'],100,0.6)
full_df['cftc_low_thr']=pd.rolling_quantile(full_df['cftc_ma_diff'],100,0.4)

def cc_2(x,u,l):
    if x>=u:
        return 1
    elif x<=l:
        return -1
    else:
        return 0

full_df['close_ma_sig']=map(cc_2,full_df['c_ma_diff'],full_df['c_up_thr'],full_df['c_low_thr'])
full_df['cftc_ma_sig']=map(cc_2,full_df['cftc_ma_diff'],full_df['cftc_up_thr'],full_df['cftc_low_thr'])


def sig(x,y):
    if x==y and x!=0:
        return x
    elif x*y==-1:
        return -x
    else:
        return 0

full_df['dir']=map(sig,full_df['close_ma_sig'],full_df['cftc_ma_sig'])

full_df['dir']=full_df['dir'].shift(1)

full_df['daily_r']=full_df['dir']*full_df['r']

full_df['cum_r']=full_df['daily_r'].cumsum()

plt.figure(figsize=(15,8))
plt.subplot(4,1,1)
plt.plot(full_df['cum_r'],label='cum_return')
plt.subplot(4,1,2)
plt.bar(full_df.index,full_df['dir'],color='orange',alpha=0.5)
plt.subplot(4,1,3)
plt.plot(full_df['close'])
plt.subplot(4,1,4)
plt.plot(full_df['cftc'])