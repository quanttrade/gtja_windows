df=read.csv('/Users/liyuefan/Documents/gtja/r.csv',stringsAsFactors = FALSE)
library(RMySQL)

conn=dbConnect(MySQL(),user='liyuefan',password='1994050306',db='gtja_intern')
dbSendQuery(conn,'set names utf8')
res=dbSendQuery(conn,'select distinct update_date, sum(hold_vol_buy) as buy from gtja_intern.zn_volume_data where rank_2<=5 group by update_date')

dat_buy=fetch(res,n=-1)
dbDisconnect(conn)

conn=dbConnect(MySQL(),user='liyuefan',password='1994050306',db='gtja_intern')
dbSendQuery(conn,'set names utf8')
res=dbSendQuery(conn,'select distinct update_date, sum(hold_vol_sell) as sell from gtja_intern.zn_volume_data where rank_3<=5 group by update_date')

dat_sell=fetch(res,n=-1)
dbDisconnect(conn)

dat_buy$update_date=as.Date(dat_buy$update_date)
dat_sell$update_date=as.Date(dat_sell$update_date)
dat=merge(dat_buy,dat_sell,by='update_date',all=FALSE)
dat$concentration=dat$buy-dat$sell

df$update_date=as.Date(df$update_date)
df=merge(df,dat,by='update_date',all=FALSE)


df$concentration=df$concentration/df$position_all
df$close_tom=c(0,df$close[1:(nrow(df)-1)])
df$rr_tom=c((diff(log(df$close_tom))),0)
for (i in 2:ncol(df)){
  df[which(df[,i]==Inf),i]=0
}

x=seq(1,nrow(df),1)
par(mfrow=c(2,1))
plot(x,df$concentration,'l')
plot(x,df$close,'l')
cor.test(df$concentration,df$rr_tom)

m=lm(rr_tom~concentration,data=df)
summary(m)
concentration=df$concentration
test=cbind(df$concentration,rep(1,nrow(df)))
test=data.frame(test)
pre=predict(m,test)

par(mfrow=c(1,1))
plot(x,df$rr_tom,'l',col='red')
lines(x,pre,'l')

concentration=df$concentration
trend=df$rr_tom
s=c()
for (i in 2:nrow(df)){
  if (concentration[i]>concentration[i-1]){
    if (trend[i]>trend[i-1]){
      s=cbind(s,1)
    }
    else{
      s=cbind(s,0)
    }
  }

  else if (concentration[i]<concentration[i-1]){
    if (trend[i]<trend[i-1]){
      s=cbind(s,1)
    }
    else{
      s=cbind(s,0)
    }
  }
}

sum(s)/length(s)


