#coding:utf-8
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


def download_data(browser,date_button,category):
    wait = ui.WebDriverWait(browser,20)
    # wait_2= ui.WebDriverWait(browser,0.5)
    wait_3= ui.WebDriverWait(browser,5)
    #点击选择日期
    wait.until(lambda driver:driver.find_elements_by_class_name(" has-data"))
    date_button.click()


    #time.sleep(5)
    #点击选择“日交易排名”（在页面中的控件id为pm）
    wait.until(lambda driver:driver.find_element_by_id('pm'))

    browser.find_element_by_id('pm').click()

    #time.sleep(5)
    #点击镍的日交易排名标签
    wait.until(lambda driver: driver.find_element_by_id("divtable"))
    wait_3.until(lambda driver:driver.find_element_by_id('li_%s'%category))
    try:
        browser.find_element_by_id('li_%s'%category).click()
        time.sleep(1)
    except:
        pass

    wait_3.until(lambda driver: driver.find_element_by_class_name("artcle-btn-04"))
    #点击下载csv文件的按钮
    browser.find_element_by_class_name("artcle-btn-04").click()



def read_csv(file_path):
    total=pd.DataFrame()
    with open(file_path) as csvfile:
        reader = csv.reader(csvfile,delimiter=':',quotechar='|')
        cnt=0
        for row in reader:
            if len(row)>0:
                row=row[0]
                temp_1=row.split(' ')
                if temp_1[0]==word_1:
                    t=[]
                    name=temp_1[1][2:]
                    t_1=temp_1[-1][:-1]
                    update_date=t_1.replace(',','')

                temp_2=row.split(',')
                if temp_2[0]==word_3:
                    t_2=[]
                    cnt=1


                if cnt==1:
                    cnt+=1
                if cnt>1:
                    temp_2=row.split(',')
                    temp_2[1]=temp_2[1].decode('gbk')
                    temp_2[1]=temp_2[1].encode('utf8')
                    temp_2[5]=temp_2[5].decode('gbk')
                    temp_2[5]=temp_2[5].encode('utf8')
                    temp_2[9]=temp_2[9].decode('gbk')
                    temp_2[9]=temp_2[9].encode('utf8')
                    #temp_2=str(filter(lambda x: len(x)>0,map(lambda y:filter(lambda x:len(x)>1,y.split(',')),temp_2))).replace('[','').replace(']','').replace("'","").split(',')
                    t_2.append(temp_2)
                    cnt+=1

                if temp_2[0]==word_2:
                    cnt=0
                    t_all=pd.DataFrame(t_2)
                    t_all['name']=name
                    t_all['update_date']=update_date
                    if len(name)>0:
                        t_all=t_all.iloc[1:-1,:]
                        total=total.append(t_all)
                    else:
                        pass
            else:
                pass




    csvfile.close()

    total=total.rename(columns={0:'rank_1',1:'company_name_1',2:'sum_vol',3:'sum_vol_chg',4:'rank_2',5:'company_name_2',6:'hold_vol_buy',7:'hold_vol_buy_chg',8:'rank_3',9:'company_name_3',10:'hold_vol_sell',11:'hold_vol_sell_chg'})
    os.remove(file_path)
    total=total.dropna(axis=0)
    return total


def month_data(all_dates,browser,file_path,category):
    monthly_data=pd.DataFrame()
    for i in range(len(set(all_dates))):
        try:
            all_dates=browser.find_elements_by_class_name("has-data")
            item=all_dates[i]
            try:
                os.remove(file_path)
            except:
                pass
            download_data(browser,item,category)
            #等待下载
            time.sleep(1)
            if os.path.exists(file_path):
            #读取下载之后的csv文件中的内容
                daily_data=read_csv(file_path)
            else:
                time.sleep(4)
                daily_data=read_csv(file_path)
                os.remove(file_path)
            #再次尝试删除下载的csv，方便下次下载
            try:
                os.remove(file_path)
            except:
                pass
            monthly_data=monthly_data.append(daily_data)

        except:
            pass
    return monthly_data



if __name__=='__main__':
    #conn = psycopg2.connect(database="gtja_intern", user="postgres", password="1994050306", host="localhost", port="5432")
    #engine = create_engine("postgresql+psycopg2://postgres:1994050306@localhost:5432/gtja_intern")
    engine = create_engine("mysql+pymysql://liyuefan:1994050306@localhost/gtja_intern?charset=utf8")
    file_path='/Users/liyuefan/Downloads/data.csv'
    category='zn'
    #engine = pymysql.connect(host='localhost',user='liyuefan',passwd='1994050306', db='gtja_intern', charset="utf8")
    word_1=u'合约代码'
    word_1=word_1.encode('gbk')
    word_2=u'合计'
    word_2=word_2.encode('gbk')
    word_3=u'名次'
    word_3=word_3.encode('gbk')
    browser=webdriver.Chrome(executable_path='/Users/liyuefan/Downloads/chromedriver')

    url='http://www.shfe.com.cn/statements/dataview.html?paramid=delaymarket_ni'

    browser.get(url)
    all_data=pd.DataFrame()
    for j in range(3):
        st=datetime.datetime.now()

        all_dates=browser.find_elements_by_class_name("has-data")
        monthly_data=month_data(all_dates,browser,file_path,category)
        all_data=all_data.append(monthly_data)
        browser.find_element_by_class_name("ui-datepicker-prev").click()
        ed=datetime.datetime.now()
        print 'month ',j,'time: ',ed-st
    all_data['update_date']=pd.to_datetime(all_data['update_date'])
    all_data['sum_vol']=all_data['sum_vol'].apply(lambda x:np.nan if x=='' else x)
    all_data['sum_vol_chg']=all_data['sum_vol_chg'].apply(lambda x:np.nan if x=='' else x)
    all_data['hold_vol_buy']=all_data['hold_vol_buy'].apply(lambda x:np.nan if x=='' else x)
    all_data['hold_vol_buy_chg']=all_data['hold_vol_buy_chg'].apply(lambda x:np.nan if x=='' else x)
    all_data['hold_vol_sell']=all_data['hold_vol_sell'].apply(lambda x:np.nan if x=='' else x)
    all_data['hold_vol_sell_chg']=all_data['hold_vol_sell_chg'].apply(lambda x:np.nan if x=='' else x)


    all_data=all_data.dropna(axis=0)
    all_data['sum_vol']=all_data['sum_vol'].apply(float)
    all_data['sum_vol_chg']=all_data['sum_vol_chg'].apply(float)
    all_data['hold_vol_buy']=all_data['hold_vol_buy'].apply(float)
    all_data['hold_vol_buy_chg']=all_data['hold_vol_buy_chg'].apply(float)
    all_data['hold_vol_sell']=all_data['hold_vol_sell'].apply(float)
    all_data['hold_vol_sell_chg']=all_data['hold_vol_sell_chg'].apply(float)
    all_data['rank_1']=all_data['rank_1'].apply(int)
    all_data['rank_2']=all_data['rank_2'].apply(int)
    all_data['rank_3']=all_data['rank_3'].apply(int)
    all_data=all_data.drop(12,axis=1)
    all_data['category']=all_data['name'].apply(lambda x:x[0:2])
    all_data['contract']=all_data['name'].apply(lambda x:x[2:])
    #all_data=all_data[all_data['update_date']==pd.to_datetime(datetime.date.today())]
    all_data=all_data.drop('name',axis=1)
    all_data=all_data[all_data['category']=='%s'%category]
    all_data=all_data.drop_duplicates()
    print all_data
    #all_data.to_csv("all_data_Cu.csv",encoding='gbk',index=False)
    all_data.to_sql("%s_volume_data"%category,engine,index=False,if_exists='append')
    browser.close()
    print 'done!'