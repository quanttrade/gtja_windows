import numpy as np
import cython


@cython.boundscheck(False)
@cython.wraparound(False)
def stop_signal(data,start_signal,stop_signal_1,stop_signal_2):
    cdef int N
    N=len(data)
    st_sig=np.nan
    ex=np.empty(N)
    for i in range(N):
        if np.isnan(data[i,start_signal])==False:
            st_sig=data[i,start_signal]
            ex[i]=np.nan
        elif np.isnan(st_sig)==False and data[i,stop_signal_1]!=st_sig:
            ex[i]=0
        elif np.isnan(st_sig)==False and np.isnan(data[i,stop_signal_2])==False and data[i,stop_signal_2]!=st_sig:
            ex[i]=0
        else:
            ex[i]=np.nan
    return ex