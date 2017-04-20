#coding: utf-8

import numpy as np
from numba import jit
import wrapt
import time


@wrapt.decorator
def timeit(func, args, kwargs):
    t=time.time()
    ans=func(*args, **kwargs)
    t=time.time()-t
    print func.__name__, t
    return ans

#x1,x2是两个多维向量，返回每个截面点的欧氏距离，x1和x2维数相同
@jit(nopython=True)
def distance(p1,p2):
    return np.sqrt(np.sum(((p1-p2)**2)))

#构造一个网格用于存储X和Y中各点之间的欧氏距离
@jit(nopython=True)
def grid(X,Y):
    #当列数为1时
    if X.shape[0]==X.size:
        lx=X.shape[0]
        wx=1
    else:
        lx=X.shape[0]
        wx=X.shape[1]
    if Y.shape[0]==Y.size:
        ly=Y.shape[0]
        wy=1
    else:
        ly=Y.shape[0]
        wy=Y.shape[1]


    # X=X.reshape((lx,wx))
    # Y=Y.reshape((ly,wy))

    if wx!=wy:
        raise IndexError('Wrong X and Y dimension')

    ws=np.arange(wx)
    for k in ws:
        s=np.std(X[0:lx,k])
        me_x=np.mean(X[0:lx,k])
        me_y=np.mean(Y[0:ly,k])
        X[:,k]=(X[0:lx,k]-me_x)/s
        Y[:,k]=(Y[0:ly,k]-me_y)/s
        # X[:,k]=X[:,k]/s
        # Y[:,k]=Y[:,k]/s


    g=np.zeros((lx,ly))
    for i in range(lx):

        for j in range(ly):
            p1=X[i,:]
            p2=Y[j,:]
            dis=distance(p1,p2)
            g[i,j]=dis
    return g
#X是最近一段日期的序列
@jit(nopython=True)
def dtw(X,Y):
    g=grid(X,Y)
    dx=g.shape[0]
    dy=g.shape[1]
    g_1=np.zeros_like(g)
    g_1[0,0]=g[0,0]
    for i in range(dx):
        for j in range(dy):
            if i==0 and j==0:
                pass
            elif i==0 and j>0:
                g_1[i,j]=g_1[i,j-1]+g[i,j]
            elif i>0 and j==0:
                g_1[i,j]=g_1[i-1,j]+g[i,j]
            else:
                d1=g_1[i,j-1]
                d2=g_1[i-1,j]
                d3=g_1[i-1,j-1]
                d_min=min(d1,d2,d3)
                g_1[i,j]=g[i,j]+d_min
    return g_1

@jit(nopython=True)
def min_dis(X,Y):
    g_1=dtw(X,Y)
    m=g_1.shape[0]
    n=g_1.shape[1]
    d1=g_1[m-1,:]
    d2=g_1[:,n-1]
    min_d1=np.min(d1)
    min_d2=np.min(d2)
    d_min=min(min_d1,min_d2)
    return d_min