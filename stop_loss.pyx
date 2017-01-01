
import numpy as np
cimport cython

@cython.boundscheck(False)
@cython.wraparound(False)
def stop_loss(trade_signal,close_high,close_low,return_rate,threshold):
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

    cum_return_L=np.empty(L,dtype=np.float32)

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

    return trade_signal, return_2

