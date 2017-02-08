library(quantmod)
all_type <- read.csv("/Users/liyuefan/Downloads/all_type.csv", sep=",")

####全品种
Pricedata<-all_type[,c(-1,-18)]
period <- nrow(Pricedata)
lambda <- 0.97
nday <- 30
Max.Loss.Each <- 0.02

Return <- Sigma <- CVaR_Up <- CVaR_Down <- matrix(0,nrow=dim(Pricedata)[1],ncol=dim(Pricedata)[2])

for(i in 1:ncol(Pricedata)){
  Return[,i] <- c(0,diff(log(Pricedata[,i])))
  Return[which(Return[,i]==Inf),i]<-NaN
  if(is.na(Return[2,i]))  begin.point<-tail(which(is.na(Return[,i])),1)+1 else begin.point<-2
  #收益率继续差分
  dr <- c(0,0,abs(diff(Return[,i]))[-1])
  #计算CVaR，每月更新一次
  for(j in (nday+3):period){
    temp <- lambda^c((nday-1):0)
    ut_hat <- sum(dr[(j-nday):(j-1)]*temp)/sum(temp)
    Sigma[j,i] <- sqrt(sum((dr[(j-nday):(j-1)]-ut_hat)^2*temp)/sum(temp))
    #从第一个非空日期开始向后数一个交易年开始每月一次
    if(j %in% seq((252+begin.point),period,22)){
      past1Y.return <- Return[(j-252):(j-1),i]
      #5%分位点CVaR为过去一年该品种的日收益率中处于左端5%的值的平均，95%同理
      CVaR_Up[j,i] <- mean(past1Y.return[past1Y.return<=quantile(past1Y.return,0.05)])
      CVaR_Down[j,i] <- mean(past1Y.return[past1Y.return>=quantile(past1Y.return,0.95)])            
    }else if(j > max(254,begin.point)){
      CVaR_Up[j,i] <- CVaR_Up[j-1,i]
      CVaR_Down[j,i] <- CVaR_Down[j-1,i]
    }
  }  
}
Return[which(is.na(Return))]<-0
#X为仓位方向信号
MA10<- MA20<-X<-matrix(0,nrow=dim(Pricedata)[1],ncol=dim(Pricedata)[2])
for(i in 1:ncol(Pricedata)){
  Price <- Pricedata[,i]
  MA10 <- SMA(Price,n=5);MA20 <- SMA(Price,n=10)
  MA10.pre<- c(0,MA10[-nrow(Pricedata)]);
  MA20.pre<- c(0,MA20[-nrow(Pricedata)]);
  X[,i]<- (MA10>MA20)*(MA10.pre<MA20.pre)+(-1)*(MA10<MA20)*(MA10.pre>MA20.pre);
  #X错位
  X[,i]=c(0,X[-nrow(Pricedata),i]);
}

Position <- PnL <- CumPnL <- Cost <- matrix(0,nrow=dim(Pricedata)[1],ncol=dim(Pricedata)[2])
#计算杠杆率
Leverage <- numeric(period)
w <- rep(0,ncol(Pricedata))
for(i in 254:period){
  
  for (j in 1:ncol(X)){
    if (X[i,j]==0) {
      X[i,j] <- X[(i-1),j]
    
    }
    else{
      X[which(is.na(X))]<-0
    }
  }
  if (sum(X[i,]!=X[i-1,])>0) w<-1/Sigma[i,]/sum(1/na.omit(Sigma[i,]))
  w[which(is.na(Sigma[i,]))]<-0
  Position[i,]<-w*X[i,]
  td <- sign(Position[i,])##whether to use CVaR_Up or CVaR_Down 
  Up <- which(td==1); Down <- which(td==-1)
  CVaR <- sum(CVaR_Up[i,Up]*Position[i,Up])+sum(CVaR_Down[i,Down]*Position[i,Down])
  if(CVaR==0) Leverage[i]<-0 else Leverage[i] <- Max.Loss.Each/abs(CVaR)
  Position[i,] <- Leverage[i]*Position[i,]
  Cost[i,] <- -0.0001*abs(Position[i,] - Position[i-1,])
  PnL[i,] <- Position[i,]*Return[i,]
  CumPnL[i,] <- CumPnL[i-1,] + PnL[i,] + Cost[i,]
}
par(mfrow=c(2,1))
CumPL <- rowSums(CumPnL)
plot(CumPL,type="l")
t1 <- tail(CumPL,1); t2 <- max(cummax(CumPL)-CumPL)
Performance <- c(t1,t2); names(Performance) <- c("Return","Max.Dw")
Performance
PL <- rowSums(PnL+Cost)
Max.Dw0 <- cummax(cumsum(PL)) - cumsum(PL)
plot(Max.Dw0,type = "l")
#####Sharpe Ratio
PL <- rowSums(PnL+Cost)
PL <- PL[-c(1:253)]
SR <- (mean(PL)*252 - 0.03)/(sd(PL)*sqrt(252))
SR


