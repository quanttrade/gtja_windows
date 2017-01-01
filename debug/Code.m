%EWRC(Equally Weighted Risk Contribution£©& CVaR calculation using
%historical daily closing price data

% Import pricedata
pricedata=xlsread('data.xlsx');
%% 
tperiod=length(pricedata);
a1=size(pricedata);
width=a1(2);
returndata=[];
for i=2:tperiod
    x=[];
    for j=1:width
        r=log(pricedata(i,j)/pricedata(i-1,j));
        x=[x r];
    end
    returndata=[returndata;x];     %Calculate daily return
end

%The following codes are used to match the return data and it's
%corresponding time. For example, the first row of returndata are used to
%indicates the return in Day 2 in the backtesting.
tperiod=length(pricedata);
line=linspace(2,tperiod,tperiod-2+1);
returndata=[returndata line'];


%The following codes are used to calculate the daily volatility using EWRC
%model. 
tperiod=length(returndata);
a1=size(pricedata);
width=a1(2);
DRdata=[];
for j=1:width
    x=[];
    for i=2:tperiod
        a=abs(returndata(i,j)-returndata(i-1,j));
        x=[x;a];
    end
    DRdata=[DRdata x];
end

tperiod=length(DRdata);
period=30;
U=[];
for i=1:width
    uu=[];
    for k=period:tperiod
        s1=0;
        for j=k-period+1:k
            e=DRdata(j,i);
            s1=s1+e*0.97^(k-j-1);
        end
        est=s1/19.9664;
    uu=[uu;est];
    end
    U=[U uu];
end                                    

tperiod=length(DRdata);
period=30;
S=[];
for i=1:width
    ss=[];
    for k=period:tperiod
        s1=0;
        for j=k-period+1:k
            e=DRdata(j,i);
            s1=s1+(e-U(k-period+1,i))^2*0.97^(k-j);
        end
        est=(s1/19.9664)^0.5;
    ss=[ss;est];
    end
    S=[S ss];
end

%The first row of S will be used in the strategy of Day 33. 
tperiod=length(pricedata);
line=linspace(33,tperiod+1,tperiod+1-33+1);
S=[S line'];

%The following codes are using the 252(one year) historical return data 
%to calculate the CVaR in the next month. 
 
tperiod=length(returndata);
Var=[];
for j=1:width
    x=[];
    for i=252:22:tperiod
        a=prctile(returndata(i-251:i,j),5);
        x=[x;a];
    end
    Var=[Var x];
end
            
CV=[];
for j=1:width
    x=[];
    a=0;
    for k=252:22:tperiod
        a=a+1;
        b=0;
        for i=k-251:k
            if returndata(i,j)<Var(a,j)
            b=b+returndata(i,j);
            end
        end
        x=[x;-b/13];
    end
    CV=[CV x];
end

CVar=[];
a2=size(CV);
m=a2(1);
for j=1:width
    x=[];
    for i=1:m
        for k=1:22
            a=CV(i,j);
            x=[x;a];
        end
    end
    CVar=[CVar x];
end

tperiod=length(pricedata);
line=linspace(253,length(CVar)+252,length(CVar));
CVar=[CVar line'];
%The first row of CVar will be used in the strategy of Day 253

%%%Trend Calculation using moving average price data.
tperiod=length(pricedata);
a1=size(pricedata);
width=a1(2);
MA_10=[];
for j=1:width
    ma=[];
    for k=10:tperiod
        A=0;
        for i=k-9:k
            A=A+pricedata(i,j);
        end
        B=A/10;
        ma=[ma;B];
    end
    MA_10=[MA_10 ma];
end

MA_30=[];
for j=1:width
    ma=[];
    for k=30:tperiod
        A=0;
        for i=k-29:k
            A=A+pricedata(i,j);
        end
        B=A/30;
        ma=[ma;B];
    end
    MA_30=[MA_30 ma];
end

MA_50=[];
for j=1:width
    ma=[];
    for k=50:tperiod
        A=0;
        for i=k-49:k
            A=A+pricedata(i,j);
        end
        B=A/50;
        ma=[ma;B];
    end
    MA_50=[MA_50 ma];
end

MA_70=[];
for j=1:width
    ma=[];
    for k=70:tperiod
        A=0;
        for i=k-69:k
            A=A+pricedata(i,j);
        end
        B=A/70;
        ma=[ma;B];
    end
    MA_70=[MA_70 ma];
end

MA_90=[];
for j=1:width
    ma=[];
    for k=90:tperiod
        A=0;
        for i=k-89:k
            A=A+pricedata(i,j);
        end
        B=A/90;
        ma=[ma;B];
    end
    MA_90=[MA_90 ma];
end

MA_110=[];
for j=1:width
    ma=[];
    for k=110:tperiod
        A=0;
        for i=k-109:k
            A=A+pricedata(i,j);
        end
        B=A/110;
        ma=[ma;B];
    end
    MA_110=[MA_110 ma];
end

MA_130=[];
for j=1:width
    ma=[];
    for k=130:tperiod
        A=0;
        for i=k-129:k
            A=A+pricedata(i,j);
        end
        B=A/130;
        ma=[ma;B];
    end
    MA_130=[MA_130 ma];
end

MA_150=[];
for j=1:width
    ma=[];
    for k=150:tperiod
        A=0;
        for i=k-149:k
            A=A+pricedata(i,j);
        end
        B=A/150;
        ma=[ma;B];
    end
    MA_150=[MA_150 ma];
end

gap=length(pricedata)-length(MA_10);
tperiod=length(MA_10);
Trend_10=[];
for j=1:width
    tt=[];
    trend=0;
    for i=2:tperiod
        if pricedata(gap+i-1,j)<MA_10(i-1,j) & pricedata(gap+i,j)>=MA_10(i,j)
           trend=1;
        end
        if pricedata(gap+i-1,j)>=MA_10(i-1,j) & pricedata(gap+i,j)<MA_10(i,j)
           trend=-1;
        end
        tt=[tt;trend];
    end
    Trend_10=[Trend_10 tt];
end

gap=length(pricedata)-length(MA_30);
tperiod=length(MA_30);
Trend_30=[];
for j=1:width
    tt=[];
    trend=0;
    for i=2:tperiod
        if pricedata(gap+i-1,j)<MA_30(i-1,j) & pricedata(gap+i,j)>=MA_30(i,j)
           trend=1;
        end
        if pricedata(gap+i-1,j)>=MA_30(i-1,j) & pricedata(gap+i,j)<MA_30(i,j)
           trend=-1;
        end
        tt=[tt;trend];
    end
    Trend_30=[Trend_30 tt];
end

gap=length(pricedata)-length(MA_50);
tperiod=length(MA_50);
Trend_50=[];
for j=1:width
    tt=[];
    trend=0;
    for i=2:tperiod
        if pricedata(gap+i-1,j)<MA_50(i-1,j) & pricedata(gap+i,j)>=MA_50(i,j)
           trend=1;
        end
        if pricedata(gap+i-1,j)>=MA_50(i-1,j) & pricedata(gap+i,j)<MA_50(i,j)
           trend=-1;
        end
        tt=[tt;trend];
    end
    Trend_50=[Trend_50 tt];
end

gap=length(pricedata)-length(MA_70);
tperiod=length(MA_70);
Trend_70=[];
for j=1:width
    tt=[];
    trend=0;
    for i=2:tperiod
        if pricedata(gap+i-1,j)<MA_70(i-1,j) & pricedata(gap+i,j)>=MA_70(i,j)
           trend=1;
        end
        if pricedata(gap+i-1,j)>=MA_70(i-1,j) & pricedata(gap+i,j)<MA_70(i,j)
           trend=-1;
        end
        tt=[tt;trend];
    end
    Trend_70=[Trend_70 tt];
end

gap=length(pricedata)-length(MA_90);
tperiod=length(MA_90);
Trend_90=[];
for j=1:width
    tt=[];
    trend=0;
    for i=2:tperiod
        if pricedata(gap+i-1,j)<MA_90(i-1,j) & pricedata(gap+i,j)>=MA_90(i,j)
           trend=1;
        end
        if pricedata(gap+i-1,j)>=MA_90(i-1,j) & pricedata(gap+i,j)<MA_90(i,j)
           trend=-1;
        end
        tt=[tt;trend];
    end
    Trend_90=[Trend_90 tt];
end

gap=length(pricedata)-length(MA_110);
tperiod=length(MA_110);
Trend_110=[];
for j=1:width
    tt=[];
    trend=0;
    for i=2:tperiod
        if pricedata(gap+i-1,j)<MA_110(i-1,j) & pricedata(gap+i,j)>=MA_110(i,j)
           trend=1;
        end
        if pricedata(gap+i-1,j)>=MA_110(i-1,j) & pricedata(gap+i,j)<MA_110(i,j)
           trend=-1;
        end
        tt=[tt;trend];
    end
    Trend_110=[Trend_110 tt];
end

gap=length(pricedata)-length(MA_130);
tperiod=length(MA_130);
Trend_130=[];
for j=1:width
    tt=[];
    trend=0;
    for i=2:tperiod
        if pricedata(gap+i-1,j)<MA_130(i-1,j) & pricedata(gap+i,j)>=MA_130(i,j)
           trend=1;
        end
        if pricedata(gap+i-1,j)>=MA_130(i-1,j) & pricedata(gap+i,j)<MA_130(i,j)
           trend=-1;
        end
        tt=[tt;trend];
    end
    Trend_130=[Trend_130 tt];
end

gap=length(pricedata)-length(MA_150);
tperiod=length(MA_150);
Trend_150=[];
for j=1:width
    tt=[];
    trend=0;
    for i=2:tperiod
        if pricedata(gap+i-1,j)<MA_150(i-1,j) & pricedata(gap+i,j)>=MA_150(i,j)
           trend=1;
        end
        if pricedata(gap+i-1,j)>=MA_150(i-1,j) & pricedata(gap+i,j)<MA_150(i,j)
           trend=-1;
        end
        tt=[tt;trend];
    end
    Trend_150=[Trend_150 tt];
end

tperiod=length(Trend_150);
T_1=[];
for j=1:width
    x=[];
    for i=1:tperiod
       a=0.2*Trend_10(i+140,j)+0.2*Trend_30(i+120,j)+0.2*Trend_50(i+100,j)+0.2*Trend_70(i+80,j)+0.2*Trend_90(i+60,j)+0*Trend_110(i+40,j)+0*Trend_130(i+20,j)+0*Trend_150(i,j);
        x=[x;a];
    end
    T_1=[T_1 x];
end

%The first row of T will be used in the strategy of Day 152
%The last row of T will be used in the day after the last day.
tperiod=length(pricedata);
line=linspace(151,tperiod,tperiod-151+1);
T_1=[T_1 line'];
    


gap=CVar(1,width+1)-T_1(1,width+1);
period=length(T_1)-1;
T=[];
for i=gap+1:period
    x=[];
    for j=1:width+1
        a=T_1(i,j);
        x=[x a];
    end
    T=[T;x];
end
gap_1=length(S)-length(T)-2;
gap_2=length(returndata)-length(T)-1;
gap_4=length(pricedata)-length(T);
a1=size(pricedata);
width=a1(2);
tperiod=length(T);
F=[]; %measures the unadjusted daily weight of each asset
X=ones( 1,width);
Delta=[];
LA=[];%measures the daily leverage rate 
Y=[];%measures the cumulative return
start=ones(1,width);
r_y=0;
C=[];
Y_perday=[];  %measures daily return of each asset
Y_per=[];%measures the loss of each asset from the day starting investment to present
LW=[];%measures the leverage rate of the portfolio
LN=[];%measures the net risk exposure.
drawdown=[];
for i=1:tperiod
    %Using the risk-parity (equally-weighted risk contribution) model to
    %decide the portfolio allocation.
    a=0;
    b=0;
    for j=1:width
        a=a+(X(j)*T(i,j))^2;
    end
    b=a^0.5;
    Delta=[Delta;b];
    ff=[];
    for j=1:width
        if b~=0
            w=X(j)*0.003/b*T(i,j)/S(i+gap_1,j);
             ff=[ff w];
        end
        if b==0
            w=0;
            ff=[ff w];
        end 
    end
    F=[F;ff];
    c=0;
    for j=1:width
        c=c+abs(F(i,j)*CVar(i,j));
    end
    if c==0
        LA=[LA;c];
    end
    if c~=0
        LA=[LA;0.027/c];
    end
    %Leverage adjustment
    %The following codes are used to calculate the trading cost.
    if i==1
        cost=0;
        for j=1:width
            cost=cost+0.0001*abs(LA(1)*F(1,j));
        end
        C=[C;cost];
    end
    if i>1
        cost=0;
        for j=1:width
            cost=cost+0.0001*abs(LA(i-1)*F(i-1,j)-LA(i)*F(i,j));
        end
        C=[C;cost];
    end
    p=0;
    for j=1:width
        p=p+abs(LA(i)*F(i,j));
    end
    LW=[LW;p];
    k=0;
    for j=1:width
        k=k+LA(i)*F(i,j);
    end
    LN=[LN;k];
    r_day=0;
    Y=[Y;exp(r_y)-cost]; 
    for j=1:width
        r_day=r_day+LA(i)*F(i,j)*(exp(returndata(i+gap_2,j))-1);
    end
    r_y=r_y+log(r_day+1);
    ff=[];
    for j=1:width
        r=Y(i)*LA(i)*F(i,j)*(exp(returndata(i+gap_2,j))-1);
        ff=[ff r];
    end
    Y_perday=[Y_perday;ff];
    rr=[];
    for j=1:width
        a=0;
        for m=start(j):i
            a=a+Y_perday(m,j);
        end
        rr=[rr a];
    end
    Y_per=[Y_per;rr];
    dd=[];
    for j=1:width
        z=0;
        draw=0;
        if i-start(j)>49
             for m=i-49:i
                 e=Y_per(m,j);
                   if e>z
                      z=e;
                   end
             end
             if z~=0
                  draw=(z-Y_per(i,j))/z;
             end
        end
        dd=[dd draw];
    end
    drawdown=[drawdown;dd];
    
    for j=1:width
        if Y_per(i,j)<0 |drawdown(i,j)>0.2
            start(j)=i;
             X(j)=0;
        end
    end
    
    H_price=[];
    for j=1:width
        a=0;
        for k=start(j)-125:i-1
            b=pricedata(k+gap_4,j);
              if b>a
                 a=b;
              end
        end
           H_price=[H_price a];
    end
    L_price=[];
    for j=1:width
        a=100000;
        for k=start(j)-125:i-1
            b=pricedata(k+gap_4,j);
            if b<a
                a=b;
            end
        end
        L_price=[L_price a];
    end
    for j=1:width
        if X(j)==0
       if pricedata(gap_4+i,j)>H_price(j) |  pricedata(gap_4+i,j)<L_price(j)
           start(j)=i;
           X(j)=1;
       end
        end
    end
end

ts=datenum('2011-07 00:00:00');
tf=datenum('2016-07 00:00:00');
t=linspace(ts,tf,length(Y));
plot(t,Y)
datetick('x','yyyy/mm','keepticks')




