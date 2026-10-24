"""
Replication of the UMD (Up Minus Down) momentum factor following
"Fact, Fiction, and Momentum Investing" (Asness, Frazzini, Israel and Moskowitz, AQR, 2014).

Data: CRSP monthly (Fama-French style), from December 1925
to 31 December 2013. NYSE, AMEX and NASDAQ stocks are used.
The data are not included in the repository due to WRDS licensing.

Method:
- Signal: cumulative return from t-12 to t-2 (skipping month t-1).
- Size: previous month's market cap, split at the NYSE median.
- Momentum: NYSE 30th and 70th percentiles, common to Small and Big (as in Ken French).
- Value-weighted portfolios:
  UMD = 1/2 (Small Win + Big Win) - 1/2 (Small Lose + Big Lose).

Validation: compared against Ken French's official UMD (F-F_Momentum_Factor.CSV,
from his Data Library). The monthly series (umd_monthly.csv) and the
cumulative return chart (umd_cumulative.png) are saved.
"""
import pandas as pd
import matplotlib.pyplot as plt
import math
dates=pd.period_range("1925-12-31", "2013-12-31", freq="M")
crspDataFrame=pd.read_csv("MonthluDataCRSPFamaFrenchStyle.csv", parse_dates=["MthCalDt"])
crspDataFrame["Month"]=crspDataFrame["MthCalDt"].dt.to_period("M")

#Remove duplicate rows (code by Claude)
crspDataFrame = crspDataFrame.drop_duplicates()
crspDataFrame = (crspDataFrame
                 .sort_values(["PERMNO", "MthCalDt", "Ticker"], na_position="last")
                 .drop_duplicates(["PERMNO", "MthCalDt"], keep="first"))


crspDataFrameSort=crspDataFrame.sort_values(by="Month")

crspMonthData=[crspDataFrameSort.loc[crspDataFrameSort["Month"]==i] for i in dates]
# Each month is indexed (and sorted) by PERMNO, to align stocks across months
crspMonthDataSortComp = [m.set_index("PERMNO").sort_index() for m in crspMonthData]

# Loop over months from 12 onwards, the first with 12 months of prior history
for i in range(12, len(crspMonthDataSortComp)):
    # Returns of each stock in months t-2 to t-12 (11 months; t-1 is skipped)
    rets = [crspMonthDataSortComp[i-j]["MthRet"] for j in range(2, 13)]
    # Joins the 11 months as columns (hence axis=1) of a dataframe (that is what pd.concat does), sorted by unique PERMNO, and computes prod(1+r) - 1 per stock; NaN if any month is missing for the PERMNO
    cumul = pd.concat(rets, axis=1).add(1).prod(axis=1, min_count=11) - 1
    # Assigns each stock in month i its cumulative return (aligned by PERMNO)
    crspMonthDataSortComp[i]["CReturn"] = cumul

# Previous month's market cap of each stock (aligned by PERMNO, like CReturn)
crspMonthDataSortComp[0]["CapLag"] = float("nan")
for i in range(1, len(crspMonthDataSortComp)):
    crspMonthDataSortComp[i]["CapLag"] = crspMonthDataSortComp[i-1]["MthCap"]

# Sorts each month by market cap, smallest to largest (NaN MthCap values go last)
crspMonthDataMtCap = [i.sort_values(by="MthCap") for i in crspMonthDataSortComp]

# NYSE stocks of each month, without NaN CapLag, sorted by previous month's size
crspNYSE = [m[m["PrimaryExch"] == "N"] for m in crspMonthDataSortComp]
crspNYSESortbyCap = [i.dropna(subset=["CapLag"]).sort_values("CapLag") for i in crspNYSE]

# Median NYSE CapLag in each month (NaN if the month is empty)
crspSizeMedian = [i.iloc[int(len(i)*0.5)]["CapLag"] if len(i) > 0 else float("nan") for i in crspNYSESortbyCap]

# Small: all stocks of the month (NYSE, AMEX, NASDAQ) with CapLag <= NYSE median
crspSmall = [crspMonthDataSortComp[i][crspMonthDataSortComp[i]["CapLag"] <= crspSizeMedian[i]] for i in range(len(crspMonthDataSortComp))]

# Big: all stocks of the month with CapLag > NYSE median
crspBig = [crspMonthDataSortComp[i][crspMonthDataSortComp[i]["CapLag"] > crspSizeMedian[i]] for i in range(len(crspMonthDataSortComp))]

# From month 12 onwards (earlier months lack 11 months of history), dropping stocks with NaN CReturn or MthRet
crspSmallSortbyCRet = [i.dropna(subset=["CReturn", "MthRet"]).sort_values("CReturn") for i in crspSmall[12:]]
crspBigSortbyCRet = [i.dropna(subset=["CReturn", "MthRet"]).sort_values("CReturn") for i in crspBig[12:]]
# NYSE stocks with CapLag and CReturn, sorted by CReturn: the 30th and 70th percentiles come from them,
# the same for Small and Big (size-independent breakpoints, as in Ken French)
crspNYSESortbyCRet = [i.dropna(subset=["CReturn"]).sort_values("CReturn") for i in crspNYSESortbyCap[12:]]

crspLoseNum = [i.iloc[int(len(i)*0.3)]["CReturn"] if len(i) > 0 else float("nan") for i in crspNYSESortbyCRet]


crspSmallLose = [crspSmallSortbyCRet[i][crspSmallSortbyCRet[i]["CReturn"] <= crspLoseNum[i]] for i in range(len(crspSmallSortbyCRet))]
crspBigLose = [crspBigSortbyCRet[i][crspBigSortbyCRet[i]["CReturn"] <= crspLoseNum[i]] for i in range(len(crspBigSortbyCRet))]


crspWinNum = [i.iloc[int(len(i)*0.7)]["CReturn"] if len(i) > 0 else float("nan") for i in crspNYSESortbyCRet]

crspSmallWin= [crspSmallSortbyCRet[i][crspSmallSortbyCRet[i]["CReturn"] >= crspWinNum[i]] for i in range(len(crspSmallSortbyCRet))]
crspBigWin = [crspBigSortbyCRet[i][crspBigSortbyCRet[i]["CReturn"] >= crspWinNum[i]] for i in range(len(crspBigSortbyCRet))]

totalMktCapSmallWin=[i["CapLag"].sum() for i in crspSmallWin]
totalMktCapBigWin=[i["CapLag"].sum() for i in crspBigWin]
totalMktCapSmallLose=[i["CapLag"].sum() for i in crspSmallLose]
totalMktCapBigLose=[i["CapLag"].sum() for i in crspBigLose]

returnSmallWin=[(crspSmallWin[i]["MthRet"]*crspSmallWin[i]["CapLag"]/totalMktCapSmallWin[i]).sum() if len(crspSmallWin[i]) > 0 else float("nan") for i in range(len(crspSmallWin))]
returnBigWin=[(crspBigWin[i]["MthRet"]*crspBigWin[i]["CapLag"]/totalMktCapBigWin[i]).sum() if len(crspBigWin[i]) > 0 else float("nan") for i in range(len(crspBigWin))]
returnSmallLose=[(crspSmallLose[i]["MthRet"]*crspSmallLose[i]["CapLag"]/totalMktCapSmallLose[i]).sum() if len(crspSmallLose[i]) > 0 else float("nan") for i in range(len(crspSmallLose))]
returnBigLose=[(crspBigLose[i]["MthRet"]*crspBigLose[i]["CapLag"]/totalMktCapBigLose[i]).sum() if len(crspBigLose[i]) > 0 else float("nan") for i in range(len(crspBigLose))]

umd=[((1/2)*(returnSmallWin[i]+returnBigWin[i]))-((1/2)*(returnSmallLose[i]+returnBigLose[i])) for i in range(len(returnBigLose))]

mu_umd=pd.Series(umd).mean()
sigma_umd=pd.Series(umd).std()

print("Mean UMD:",mu_umd ," Std UMD:", sigma_umd)

# Each umd value corresponds to a month from 12 onwards (same order as dates[12:])
umdSeries=pd.Series(umd, index=dates[12:]).dropna()
umdSeries.to_csv("umd_monthly.csv", header=["UMD"])

# Ken French's official UMD (F-F_Momentum_Factor.CSV): monthly rows only (date YYYYMM), in %
frenchMom={}
with open("F-F_Momentum_Factor.CSV") as f:
    for line in f:
        fields=line.strip().split(",")
        if len(fields)==2 and fields[0].strip().isdigit() and len(fields[0].strip())==6:
            date=fields[0].strip()
            frenchMom[pd.Period(year=int(date[:4]), month=int(date[4:]), freq="M")]=float(fields[1])/100
frenchSeries=pd.Series(frenchMom)

# Months common to both series
common=umdSeries.index.intersection(frenchSeries.index)
umdCommon=umdSeries[common]
frenchCommon=frenchSeries[common]

# Annualised metrics: mean x12, volatility x square root of 12; UMD is long-short, so the Sharpe ratio does not subtract the risk-free rate
for name, series in [("Replication", umdCommon), ("Ken French", frenchCommon)]:
    mean=series.mean()*12
    vol=series.std()*math.sqrt(12)
    print(name, "| Annual mean:", round(mean*100, 2), "% | Annual vol:", round(vol*100, 2), "% | Sharpe:", round(mean/vol, 2))
print("Correlation replication-French:", round(umdCommon.corr(frenchCommon), 4), "| Months:", len(common), "(", common[0], "-", common[-1], ")")

# Cumulative return of $1 invested in each series (log scale)
plt.figure(figsize=(10, 5))
plt.plot(common.to_timestamp(), (1+umdCommon).cumprod().values, label="Replication")
plt.plot(common.to_timestamp(), (1+frenchCommon).cumprod().values, label="Ken French", linestyle="--")
plt.yscale("log")
plt.title("UMD: cumulative return")
plt.ylabel("Value of $1 (log scale)")
plt.legend()
plt.tight_layout()
plt.savefig("umd_cumulative.png", dpi=150)
plt.show()
