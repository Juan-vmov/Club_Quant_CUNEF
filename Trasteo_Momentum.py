import pandas as pd
import matplotlib as plt
import math
fechas=pd.period_range("1925-12-31", "2013-12-31", freq="M")
crspDataFrame=pd.read_csv("MonthluDataCRSPFamaFrenchStyle.csv", parse_dates=["MthCalDt"])
crspDataFrame["Mes"]=crspDataFrame["MthCalDt"].dt.to_period("M")

#Eliminar filas duplicadas (Código de Claude)
n_antes = len(crspDataFrame)
crspDataFrame = crspDataFrame.drop_duplicates()
quedan = crspDataFrame.duplicated(["PERMNO", "MthCalDt"], keep=False).sum()
dup = crspDataFrame[crspDataFrame.duplicated(["PERMNO", "MthCalDt"], keep=False)]
crspDataFrame = (crspDataFrame
                 .sort_values(["PERMNO", "MthCalDt", "Ticker"], na_position="last")
                 .drop_duplicates(["PERMNO", "MthCalDt"], keep="first"))


crspDataFrameSort=crspDataFrame.sort_values(by="Mes")

crspMonthData=[crspDataFrameSort.loc[crspDataFrameSort["Mes"]==i] for i in fechas]
# Cada mes pasa a estar indexado por PERMNO (y ordenado), para alinear acciones entre meses
crspMonthDataSortComp = [m.set_index("PERMNO").sort_index() for m in crspMonthData]

# Recorremos los meses desde el 12, el primero con 12 meses de historia previa
for i in range(12, len(crspMonthDataSortComp)):
    # Retornos de cada acción en los meses t-2 a t-12 (11 meses; se salta t-1)
    rets = [crspMonthDataSortComp[i-j]["MthRet"] for j in range(2, 13)]
    # Une los 11 meses como columnas (por eso axis=1) de un dataframe (para eso sirve pd.concat), ordenadas por PERMNO único, calcula prod(1+r) - 1 por acción; NaN si falta algún mes en el PERMNO
    cumul = pd.concat(rets, axis=1).add(1).prod(axis=1, min_count=11) - 1
    # Asigna a cada acción del mes i su retorno acumulado (se alinea por PERMNO)
    crspMonthDataSortComp[i]["CReturn"] = cumul

# Capitalización del mes anterior de cada acción (se alinea por PERMNO, igual que CReturn)
crspMonthDataSortComp[0]["CapLag"] = float("nan")
for i in range(1, len(crspMonthDataSortComp)):
    crspMonthDataSortComp[i]["CapLag"] = crspMonthDataSortComp[i-1]["MthCap"]

# Ordena cada mes por capitalización de menor a mayor (los NaN de MthCap quedan al final)
crspMonthDataMtCap = [i.sort_values(by="MthCap") for i in crspMonthDataSortComp]

# Acciones del NYSE de cada mes, sin CapLag NaN, ordenadas por tamaño del mes anterior
crspNYSE = [m[m["PrimaryExch"] == "N"] for m in crspMonthDataSortComp]
crspNYSESortbyCap = [i.dropna(subset=["CapLag"]).sort_values("CapLag") for i in crspNYSE]

# Valor de la mediana de CapLag del NYSE en cada mes (NaN si el mes está vacío)
crspSizeMedian = [i.iloc[int(len(i)*0.5)]["CapLag"] if len(i) > 0 else float("nan") for i in crspNYSESortbyCap]

# Small: todas las acciones del mes (NYSE, AMEX, NASDAQ) con CapLag <= mediana NYSE
crspSmall = [crspMonthDataSortComp[i][crspMonthDataSortComp[i]["CapLag"] <= crspSizeMedian[i]] for i in range(len(crspMonthDataSortComp))]
crspSmallNYSE = [m[m["PrimaryExch"] == "N"] for m in crspSmall]

# Big: todas las acciones del mes con CapLag > mediana NYSE
crspBig = [crspMonthDataSortComp[i][crspMonthDataSortComp[i]["CapLag"] > crspSizeMedian[i]] for i in range(len(crspMonthDataSortComp))]
crspBigNYSE = [m[m["PrimaryExch"] == "N"] for m in crspBig]

# Desde el mes 12 (los anteriores no tienen 11 meses de historia) y sin acciones con CReturn o MthRet NaN
crspSmallSortbyCRet = [i.dropna(subset=["CReturn", "MthRet"]).sort_values("CReturn") for i in crspSmall[12:]]
crspBigSortbyCRet = [i.dropna(subset=["CReturn", "MthRet"]).sort_values("CReturn") for i in crspBig[12:]]
crspSmallNYSE = [i.dropna(subset=["CReturn"]).sort_values("CReturn") for i in crspSmallNYSE[12:]]
crspBigNYSE = [i.dropna(subset=["CReturn"]).sort_values("CReturn") for i in crspBigNYSE[12:]]

crspSmallLoseNum = [i.iloc[int(len(i)*0.3)]["CReturn"] if len(i) > 0 else float("nan") for i in crspSmallNYSE]
crspBigLoseNum = [i.iloc[int(len(i)*0.3)]["CReturn"] if len(i) > 0 else float("nan") for i in crspBigNYSE]


crspSmallLose = [crspSmallSortbyCRet[i][crspSmallSortbyCRet[i]["CReturn"] <= crspSmallLoseNum[i]] for i in range(len(crspSmallSortbyCRet))]
crspBigLose = [crspBigSortbyCRet[i][crspBigSortbyCRet[i]["CReturn"] <= crspBigLoseNum[i]] for i in range(len(crspBigSortbyCRet))]


crspSmallWinNum = [i.iloc[int(len(i)*0.7)]["CReturn"] if len(i) > 0 else float("nan") for i in crspSmallNYSE]
crspBigWinNum = [i.iloc[int(len(i)*0.7)]["CReturn"] if len(i) > 0 else float("nan") for i in crspBigNYSE]

crspSmallWin= [crspSmallSortbyCRet[i][crspSmallSortbyCRet[i]["CReturn"] >= crspSmallWinNum[i]] for i in range(len(crspSmallSortbyCRet))]
crspBigWin = [crspBigSortbyCRet[i][crspBigSortbyCRet[i]["CReturn"] >= crspBigWinNum[i]] for i in range(len(crspBigSortbyCRet))]

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

print("Media UMD:",mu_umd ," Std UMD:", sigma_umd)



