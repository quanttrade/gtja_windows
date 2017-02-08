require(graphics)

spec.ar(lh)

spec.ar(ldeaths)
spec.ar(ldeaths, method = "burg")

spec.ar(log(lynx))
spec.ar(log(lynx), method = "burg", add = TRUE, col = "purple")
spec.ar(log(lynx), method = "mle", add = TRUE, col = "forest green")
spec.ar(log(lynx), method = "ols", add = TRUE, col = "blue")


df=read.csv('/Users/liyuefan/Documents/gtja/all_assets_for_R.csv',stringsAsFactors = F)
for (i in 2:ncol(df)){
  if (i==2){
    x=c(1:nrow(df))
    plot(x,df[,i],'l')
  }
  else{
    x=c(1:nrow(df))
    line(x,df[,i])
  }

}



df$update_date=as.Date(df$update_date)

cu=na.omit(df$CU)
cu=cu[1700:1950]
pacf(cu)
acf(cu)

spec.ar(cu,method='burg')
cu

