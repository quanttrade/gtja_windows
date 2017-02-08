#coding: utf-8


import numpy as np
import pandas as pd
import urllib2
import bs4
import os
from multiprocessing import Pool
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')


def execute(page_number):
    url = 'https://www.quantnet.com/tracker/?page=%s' % page_number
    req = urllib2.urlopen(url)
    page = req.read()
    page = bs4.BeautifulSoup(page)
    p1 = page.find_all(class_='applicationListItem')
    total = []
    for r in p1:
        cd = r.children
        tmp = []
        for k in cd:
            if len(k) > 1:
                ks = k.stripped_strings

                for ik in ks:
                    tmp.append(ik)
        tmp_ = []

        tmp_.append(tmp[0])

        tmp[1] = tmp[1].replace('(', '').replace(')', '')
        tmp_.append(tmp[1])

        tmp_.append(tmp[2])

        tmp_.append(tmp[5])

        try:
            tmp[6] = int(tmp[6])
            tmp_.append(tmp[6])
        except:
            tmp_.append(np.nan)

        try:
            tmp[7] = int(tmp[7])
            tmp_.append(tmp[7])
        except:
            tmp_.append(np.nan)

        try:
            tmp[8] = float(tmp[8])
            tmp_.append(tmp[8])
        except:
            tmp_.append(np.nan)

        tmp[9] = pd.to_datetime(tmp[9])
        tmp_.append(tmp[9])
        if tmp[10] == u'Pending' or tmp[10] == u'Waitlist' and tmp[11][0] != '(':
            tmp_.append(pd.to_datetime('1970-01-01'))
            tmp_.append(tmp[10])
            tmp[11] = tmp[11].split(': ')[1]
            tmp[11] = tmp[11].replace(')', '')
            tmp[11] = pd.to_datetime(tmp[9]) + np.timedelta64(tmp[11], 'D')

            tmp_.append(tmp[11])

            tmp_.append(tmp[16])

        elif tmp[10] == u'Pending' or tmp[10] == u'Waitlist' and tmp[11][0:2] == '(D':
            tmp_.append(pd.to_datetime('1970-01-01'))
            tmp_.append(tmp[10])
            tmp[11] = tmp[11].split(': ')[1]
            tmp[11] = tmp[11].replace(')', '')
            tmp[11] = pd.to_datetime(tmp[9]) + np.timedelta64(tmp[11], 'D')

            tmp_.append(tmp[11])

            tmp_.append(tmp[16])

        elif tmp[10] == u'Pending' or tmp[10] == u'Waitlist' and tmp[11][0] == '(' and tmp[11][1] != 'D':
            tmp_.append(pd.to_datetime('1970-01-01'))
            tmp_.append(tmp[10])
            tmp[12] = tmp[12].split(': ')[1]
            tmp[12] = tmp[12].replace(')', '')
            tmp[12] = pd.to_datetime(tmp[9]) + np.timedelta64(tmp[12], 'D')

            tmp_.append(tmp[12])

            tmp_.append(tmp[16])



        elif tmp[10][0:3] == u'INT':
            int_time = tmp[10].split(': ')[1]
            tmp_.append(pd.to_datetime(int_time))
            tmp_.append(tmp[11])
            if tmp[12][0:2] == '(D':
                tmp[12] = tmp[12].split(': ')[1]
                tmp[12] = tmp[12].replace(')', '')
                tmp[12] = pd.to_datetime(tmp[9]) + np.timedelta64(tmp[12], 'D')

                tmp_.append(tmp[12])
            else:
                tmp[12] = tmp[12].replace('(', '').replace(')', '')
                tmp[12] = pd.to_datetime(tmp[12])
                tmp_.append(tmp[12])

            tmp_.append(tmp[17])
        else:

            tmp_.append(pd.to_datetime('1970-01-01'))
            tmp_.append(tmp[10])
            tmp[11] = tmp[11].replace('(', '').replace(')', '')

            tmp[11] = pd.to_datetime(tmp[11])
            tmp_.append(tmp[11])

            tmp_.append(tmp[17])

        total.append(tmp_)
    df = pd.DataFrame(total, columns=['program', 'full_part', 'user_name', 'ugpa', 'gre_q',
                                      'gre_v', 'gre_aw', 'submitted', 'interview', 'result', 'update_date', 'note'])
    return df

def execute_sql(page_number,engine):
    try:

        df=execute(page_number)
        df.to_sql('quant_net_data',engine,index=False,if_exists='append')
        print 'page %s succeeded'%page_number
    except:
        print 'page %s failed'%page_number
        pass


if __name__=='__main__':
    engine = create_engine("mysql+pymysql://liyuefan:1994050306@localhost/gtja_intern?charset=utf8")
    print('Parent process %s.' % os.getpid())
    p = Pool(4)
    for i in range(1,265):
        p.apply_async(execute_sql, args=(i,engine,))
    print('Waiting for all subprocesses done...')
    p.close()
    p.join()
    print('All subprocesses done.')