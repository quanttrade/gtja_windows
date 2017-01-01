#! /Users/liyuefan/anaconda2/bin/python
#  coding: utf-8



from selenium import webdriver
import time
import pandas as pd
import os
import selenium.webdriver.support.ui as ui
import csv
import datetime
from sqlalchemy import create_engine
import numpy as np
import pymysql
from selenium.webdriver.support.select import Select
from bs4 import BeautifulSoup


# In[39]:

def Read_row(soup):
    soup=BeautifulSoup(str(soup))
    tds=soup.find_all('td')
    if tds[0].string==u'总计':
        pass
    elif tds[0].string is None:
        pass
    else:
        temp=[]
        for i in range(len(tds)):
            temp.append(tds[i].string)
        return temp


# In[40]:

def Read_page(browser,contract,update_date):
    soup=BeautifulSoup(browser.page_source)
    tbs=soup.find_all(name='tr')
    tbs=tbs[5:]
    lines=map(Read_row,tbs)
    lines=filter(lambda x: x is not None, lines)
    table=pd.DataFrame(lines)
    table=table.rename(columns={0:'rank_1',1:'company_name_1',2:'sum_vol',3:'sum_vol_chg',
                                4:'rank_2',5:'company_name_2',6:'hold_vol_buy',7:'hold_vol_buy_chg',
                                8:'rank_3',9:'company_name_3',10:'hold_vol_sell',11:'hold_vol_sell_chg',
                                })
    table['contract']=contract
    table['update_date']=update_date
    table=table.dropna(axis=0)
    return table


# In[41]:

def Contract(update_date,category):
    month=update_date.month
    year=update_date.year
    
    if month==1:
        temp=['%s%s%s'%(category,str(year)[2:],'05'),'%s%s%s'%(category,str(year)[2:],'09')]
    elif month==5:
        temp=['%s%s%s'%(category,str(year)[2:],'09'),'%s%s%s'%(category,str(year+1)[2:],'01')]
    elif month==9:
        temp=['%s%s%s'%(category,str(year+1)[2:],'01'),'%s%s%s'%(category,str(year+1)[2:],'05')]
    elif month>1 and month<5:
        temp=['%s%s%s'%(category,str(year)[2:],'05'),'%s%s%s'%(category,str(year)[2:],'09'),'%s%s%s'%(category,str(year+1)[2:],'01')]
    elif month>5 and month<9:
        temp=['%s%s%s'%(category,str(year)[2:],'09'),'%s%s%s'%(category,str(year+1)[2:],'01'),'%s%s%s'%(category,str(year+1)[2:],'05')]
    elif month>9:
        temp=['%s%s%s'%(category,str(year+1)[2:],'01'),'%s%s%s'%(category,str(year+1)[2:],'05'),'%s%s%s'%(category,str(year+1)[2:],'09')]
    return temp


# In[42]:

def execute(update_date,browser,category):
    wait=ui.WebDriverWait(browser,5)
    update_date=pd.to_datetime(update_date)
    date_input=str(update_date.date()).replace('-','')
    browser.switch_to_window(browser.window_handles[0])
    #wait.until(lambda driver:driver.find_element_by_id('trade_date'))
    browser.find_element_by_id('trade_date').click()
    
    contract_list=Contract(update_date,category)
    
    
    browser.find_element_by_id('trade_date').clear()
    browser.find_element_by_id('trade_date').send_keys(date_input)
    daily_data=pd.DataFrame()
    contract=u'全部合约'
#     for contract in contract_list:
    browser.switch_to_window(browser.window_handles[0])
    
    
#     browser.find_element_by_id('variety').click()
    Select(browser.find_element_by_id('variety')).select_by_value(category)

    browser.find_element_by_id('contract_id').click()
    browser.find_element_by_id('contract_id').clear()
#     browser.find_element_by_id('contract_id').send_keys(contract)
    browser.find_element_by_class_name("button").click()
    browser.switch_to_window(browser.window_handles[-1])
    wait.until(lambda driver:driver.find_element_by_tag_name('table'))
#         time.sleep(3)
    data_per_contract=Read_page(browser,contract,update_date)
    daily_data=daily_data.append(data_per_contract)
    browser.close()
    return daily_data


# In[49]:

if __name__=='__main__':
    engine = create_engine("mysql+pymysql://liyuefan:1994050306@localhost/gtja_intern?charset=utf8")
    url='http://218.25.154.81/PublicWeb/MainServlet?action=Pu00021_search'
    browser=webdriver.Chrome(executable_path='/Users/liyuefan/Downloads/chromedriver')
    category='i'
    browser.get(url)
    browser.find_element
    # date_start=pd.to_datetime('2013-01-01')
    date_start=pd.to_datetime(datetime.date.today())
    date_end=pd.to_datetime(datetime.date.today())
    Date_range=pd.date_range(date_start,date_end)
    for day in Date_range:
        st=datetime.datetime.now()
        browser.switch_to_window(browser.window_handles[0])
        browser.refresh()
        try:
            daily_data=execute(day,browser,category)
        except:
            browser.get(url)
            daily_data=execute(day,browser,category)
        daily_data.to_sql('%s_volume_data'%category,engine,index=False,if_exists='append')
        ed=datetime.datetime.now()
        print day,'\t','time used: ','\t',ed-st,'done! '

        


# In[ ]:



