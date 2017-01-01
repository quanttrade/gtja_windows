Sys.setenv(TZ="asia/shanghai")
Sys.setlocale("LC_TIME","us")

library(WindR)
w.start()


w_wsi_data<-w.wsi("NI1701.SHF","open,close,volume,pct_chg,oi","2016-10-19 00:00:00","2016-10-19 23:59:59")

str(w_wsi_data)

w.close()
#############################################################
P=abs(w_wsi_data$Data$pctchange)/sqrt(w_wsi_data$Data$volume)
P_vol=data.frame(P,w_wsi_data$Data)
P_vol_sort=P_vol[order(P_vol$P,decreasing=TRUE),]
amt_daily=sum(na.omit(P_vol_sort$volume))

summ_vol=0
i=0
while(summ_vol<=0.1*amt_daily){
  i=i+1
  summ_vol=P_vol_sort[i,5]+summ_vol
}

P_vol_selected=P_vol_sort[1:i,]

P_star=sum(P_vol_selected$pctchange)
#############################################################
Q=abs(diff(w_wsi_data$Data$position))/sqrt(w_wsi_data$Data$volume)[2:length(w_wsi_data$Data$volume)]

Q_vol=data.frame(Q,w_wsi_data$Data[2:length(w_wsi_data$Data$volume),],diff(w_wsi_data$Data$position))
Q_vol_sort=Q_vol[order(Q_vol$Q,decreasing=TRUE),]
Q_amt_daily=sum(na.omit(Q_vol_sort$volume))

summ_vol=0
i=0
while(summ_vol<=0.1*Q_amt_daily){
  i=i+1
  summ_vol=Q_vol_sort[i,5]+summ_vol
}

Q_vol_selected=Q_vol_sort[1:i,]

Q_star=sum(Q_vol_selected$diff.w_wsi_data.Data.position.)


P_star

Q_star

update_date=as.Date(w_wsi_data$Data$DATETIME,tz='asia/shanghai')


