#coding: utf-8

import numpy as np
import time
cimport cython



@cython.boundscheck(False)
@cython.wraparound(False)
def distance(p1,p2):
    return np.sqrt(np.sum(((p1-p2)**2)))

@cython.boundscheck(False)
@cython.wraparound(False)
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


    X=X.reshape((lx,wx))
    Y=Y.reshape((ly,wy))

    if wx!=wy:
        raise IndexError('Wrong X and Y dimension')

    for k in range(wx):
        s=np.std(X[:,k])
        X[:,k]=X[:,k]/s
        Y[:,k]=Y[:,k]/s

    g=np.zeros((lx,ly))
    for i in range(lx):

        for j in range(ly):
            p1=X[i,:]
            p2=Y[j,:]
            dis=distance(p1,p2)
            g[i,j]=dis
    return g


@cython.boundscheck(False)
@cython.wraparound(False)
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
                d_min=np.min((d1,d2,d3))
                g_1[i,j]=g[i,j]+d_min
    return g_1

@cython.boundscheck(False)
@cython.wraparound(False)
def min_dis(X,Y):
    g_1=dtw(X,Y)
    m=g_1.shape[0]
    n=g_1.shape[1]
    d1=g_1[m-1,:]
    d2=g_1[:,n-1]
    d1=list(d1)
    d2=list(d2)
    d1.extend(d2)
    d_min=np.min(d1)
    return d_min