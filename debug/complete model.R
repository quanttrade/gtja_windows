Pricedata <- read.csv("/Users/liyuefan/Documents/gtja/debug/Pricedata.csv", sep=";")
library("quantmod")
library("PerformanceAnalytics")
Date<-seq(1,nrow(Pricedata),1)
type<-length(Pricedata)
period<-nrow(Pricedata)
nday<-30
lambda<-0.97 
sigma_s<-Lev<-Trend<-CVaR<-Rate<-as.data.frame(Date)
for(i in 1:type){
  price<-Pricedata[-period,i]
  price_1<-Pricedata[-1,i]
  rate<-log(price_1/price)
  rate<-c(0,rate)
  rate_1<-rate[-1]
  eval(parse(text=paste(paste("Rate$type_",i,sep=""),"<-rate",sep=" ")))
  delta<-abs(rate_1-rate[-(length(rate))])
  delta<-c(0,delta)
  order<-seq(0,29,1)
  u<-numeric(length(delta))
  sigma<-numeric(length(delta))
  for(t in (nday+3):(length(delta))) {
    delta_order<-delta[rev(seq(t-30,t-1,1))]
    sum_u<-sum(lambda^(order)*delta_order)
    sum_lambda<-sum(lambda^(order))
    u[t]<-sum_u/sum_lambda
    sum_sigma<-sum(lambda^(order)*((delta_order-u[t])^2))
    sigma[t]<-sqrt(sum_sigma/sum_lambda)
    }
    eval(parse(text=paste(paste("sigma_s$type_",i,sep=""),"<-sigma",sep=" ")))
#####CVaR#####
  order_22<-seq(2,length(rate)-251,22)
  ave_rate<-leverage<-numeric(length(order_22))
  for(h in 1:length(order_22)){
  ave_rate[h]<-mean(sort(rate[order_22[h]:(order_22[h]+251)])[1:13])
  }  
  lev<-c(rep(0,252),rep(abs(0.023/ave_rate),each=22))
  eval(parse(text=paste(paste("Lev$type_",i,sep=""),"<-lev[1:nrow(Pricedata)]",sep=" ")))

  ave_rate<-c(rep(0,252),rep(ave_rate,each=22))
  eval(parse(text=paste(paste("CVaR$type_",i,sep=""),"<-ave_rate[1:nrow(Pricedata)]",sep=" ")))
#####end#####

#####MA method#####
pricetimeseries<-ts(Pricedata[i])
T<-dlr<-cost<-Y<-r_day<-numeric(nrow(Pricedata))
#####??weight of 110,130,150 equals to 0 #####
for(l in seq(10,90,20)){
  #####10-90 days with weights of 0.2#####
  MA<-SMA(pricetimeseries,n=l)
  MA<-MA-pricetimeseries
  trend<-numeric(nrow(Pricedata))
  for(n in (l+1):nrow(Pricedata)){
    if (MA[n-1]>0 && MA[n]<=0)
      trend[n]<-1
    else if (MA[n-1]<=0 && MA[n]>0)
      trend[n]<--1
    else trend[n]<-trend[n-1]
  }
  T<-T+0.2*trend}
  eval(parse(text=paste(paste("Trend$type_",i,sep=""),"<-T",sep=" ")))}
Trend<-Trend[,-1]
sigma_s<-sigma_s[,-1]
CVaR<-CVaR[,-1]
Rate<-Rate[,-1]
Lev<-Lev[,-1]
X<-rep(1,14)
Stoppoint<-rep(253,14)
w<-Y_perday<-Y_per<-as.data.frame(matrix(nrow=nrow(Trend),ncol=type))
draw<-as.data.frame(matrix(data=0,nrow=nrow(Trend),ncol=type))
Stop<-as.data.frame(matrix(data=1,nrow=nrow(Trend),ncol=type))
r_y<-0


#####begin from day 252?#####
for (f in 253:(nrow(Trend)-1)){
    Delta<-sqrt(sum((X*Trend[f,])^2))  
    if (Delta==0) w[f,]<-rep(0,14) else w[f,]<-X*0.003/Delta*Trend[f,]/sigma_s[f,]
    ###dlr--daily leverage rate###
   if (sum(abs(w[f,]*CVaR[f,]))!=0) 
      dlr[f]<-0.027/sum(abs(w[f,]*CVaR[f,]))
    else dlr[f]<-0
    dlr[252]<-0
    w[252,]<-rep(1,14)
    cost[f]<-sum(0.0001*abs(dlr[f-1]*w[f-1,]-dlr[f]*w[f,]))
    Y[f]<-exp(r_y)-cost[f]
    r_day[f]<-sum(dlr[f]*w[f,]*(exp(Rate[f,])-1))
    r_y<-r_y+log(r_day[f]+1)
    ####why for Y[f]####
    Y_perday[f,]<-Y[f]*dlr[f]*w[f,]*(exp(Rate[f,])-1)
    for(i in 1:14){
    Y_per[f,i]<-sum(na.omit(Y_perday[Stoppoint[i]:f,i]))
    if (f>49+Stoppoint[i]) {
      if(max(Y_per[(f-49):f,i])==0) draw[f,i]<-0
      else draw[f,i]<-(max(Y_per[(f-49):f,i])-Y_per[f,i])/max(Y_per[(f-49):f,i])}
    if (draw[f,i]>0.2|Y_per[f,i]<0){
    Stoppoint[i] <- f
    X[i] <- 0}
    ####f+1 right?####
    if (Pricedata[f+1,i]>max(Pricedata[(Stoppoint[i]-124):f,i]) 
        | Pricedata[f+1,i]<min(Pricedata[(Stoppoint[i]-124):f,i]))
    { X[i]<-1 
    Stoppoint[i]<-f}
    }
}

#####only 1/n for each type#####
date<-as.Date(seq(15065,15065+1737-1,1))
Price1<-numeric(1737)
for(j in 1:1737){
Price1[j]<-sum(Pricedata[j,])/14}
return1<-as.data.frame(CalculateReturns(ts(Price1),method ="log" ))

rownames(return1)<-date

#####risk-parity#####
date<-as.Date(seq(15065,15065+1737-1,1))
Price2<-numeric(1737)
for(j in 1:1737){
  Price2[j]<-sum(Pricedata[j,]*(Lev[j,]/sum(Lev[j,])))}
return2<-as.data.frame(CalculateReturns(ts(Price2),method ="log" ))
#####risk parity&trend-following#####



return3<-r_day
return3[which(return3==0)]<-NA
return3<-as.data.frame(return3)
rownames(return3)<-date

charts.PerformanceSummary(cbind(return3,return1))
return1[is.na(return1$x),1]<-0
return2[is.na(return2$x),1]<-0
return3[is.na(return3$return3),1]<-0
a<-cumsum(na.omit(return1))
b<-cumsum(na.omit(return2))
c<-cumsum(na.omit(return3))
plot(c$return3,type="l")
lines(b$x)
lines(a$x)

data=read.csv('/Users/liyuefan/Downloads/Indices_history.csv')
str(data)

