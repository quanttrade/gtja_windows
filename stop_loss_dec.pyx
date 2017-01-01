
import numpy as np
cimport cython
cimport numpy as np

@cython.boundscheck(False)
@cython.wraparound(False)
def np.ndarray[np.float32, ndim=2] _stop_loss(np.ndarray[np.float32,ndim=1] trade_signal,np.ndarray[np.float32,ndim=1] close_high,np.ndarray[np.float32,ndim=1] close_low,np.ndarray[np.float32,ndim=1] return_rate,double threshold):
    cdef int L
    return_mat=trade_signal*return_rate
    return_=return_mat
    L=len(return_)

    if trade_signal[0]>0:
        extreme_=close_low
    elif trade_signal[0]<0:
        extreme_=close_high
    elif trade_signal[0]==0:
        extreme_=np.zeros(L)

    cdef double cum_return
    cdef np.ndarray[np.float32,ndim=1] cum_return_L

    for i in range(L-1):
        cum_return=sum(return_[0:i])
        cum_return_L[i]=cum_return
        if i==0:
            return_[i]=return_[i]-0.0005
        else:
            pass
        if i==0 and cum_return+extreme_[i]<=threshold:
            trade_signal[i+1]=0
            return_rate[i]=threshold
            return_rate[i]=return_rate[i]-0.001
        elif i>=1 and cum_return+extreme_[i]<=threshold:
            trade_signal[i+1]=0
            return_rate[i]=threshold-cum_return_L[i-1]
            return_rate[i]=return_rate[i]-0.001
        else:
            pass
    r_matrix_2=trade_signal*return_rate
    return_2=r_matrix_2
    mat=np.ndarray[np.float32, ndim=2]
    mat[:,0]=trade_signal
    mat[:,1]=return_2
    return mat

def stop_loss(trade_signal,close_high,close_low,return_rate,threshold=-0.04):
    return _stop_loss(trade_signal,close_high,close_low,return_rate,threshold)

