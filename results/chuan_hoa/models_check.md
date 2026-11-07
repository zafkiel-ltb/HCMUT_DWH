# Kiểm định mô hình trên 4 fold Bảng 3.12 (dữ liệu từ CompanyX_DW)

g = 0.4115, r = 0.1, c = 10.0, B = 40000. Đặc trưng: ['Recency', 'Frequency', 'Monetary', 'Orders90', 'Orders180', 'Tenure', 'Share_Bikes', 'Share_Accessories', 'Share_Clothing', 'BikeBuyer', 'NSub']

## 1. Theo từng mốc: 3 điều kiện mục 3.4.6

         E                  model    auc  brier  brier_const   ci_lo   ci_hi        Z    K  Z_vonly   dk1   dk2   dk3
2013-12-15            MLP (32,16) 0.7199 0.1337       0.1492  0.0014  0.0299 290319.0 4000 281432.0  True  True  True
2013-12-15 Cây Gini sâu 4, lá 400 0.7035 0.1349       0.1492 -0.0131  0.0101 288505.0 4000 281432.0  True  True  True
2013-12-15    Naive Bayes rời rạc 0.7099 0.1342       0.1492 -0.0041  0.0152 292046.0 4000 281432.0  True  True  True
2013-12-15       Logistic one-hot 0.5733 0.1666       0.1492 -0.1480 -0.1121 279839.0 4000 281432.0 False False False
2013-12-15              Lớp đa số 0.5000 0.1492       0.1492 -0.2179 -0.1924 281432.0 4000 281432.0 False False False
2013-12-15      Recency đảo chiều 0.7047 0.2724       0.1492  0.0000  0.0000 239002.0 4000 281432.0  True False False
2014-01-15            MLP (32,16) 0.7357 0.1328       0.1494  0.0091  0.0308 290012.0 4000 276413.0  True  True  True
2014-01-15 Cây Gini sâu 4, lá 400 0.6872 0.1370       0.1494 -0.0393 -0.0187 290450.0 4000 276413.0 False  True  True
2014-01-15    Naive Bayes rời rạc 0.7203 0.1292       0.1494 -0.0046  0.0123 293085.0 4000 276413.0  True  True  True
2014-01-15       Logistic one-hot 0.6596 0.1474       0.1494 -0.0695 -0.0450 285311.0 4000 276413.0 False  True  True
2014-01-15              Lớp đa số 0.5000 0.1494       0.1494 -0.2286 -0.2035 276413.0 4000 276413.0 False False False
2014-01-15      Recency đảo chiều 0.7161 0.2690       0.1494  0.0000  0.0000 253929.0 4000 276413.0  True False False
2014-02-15            MLP (32,16) 0.7753 0.1224       0.1476  0.0382  0.0581 289820.0 4000 264034.0  True  True  True
2014-02-15 Cây Gini sâu 4, lá 400 0.7010 0.1335       0.1476 -0.0346 -0.0185 288749.0 4000 264034.0 False  True  True
2014-02-15    Naive Bayes rời rạc 0.7286 0.1199       0.1476 -0.0074  0.0092 293156.0 4000 264034.0  True  True  True
2014-02-15       Logistic one-hot 0.7201 0.1361       0.1476 -0.0160  0.0016 274227.0 4000 264034.0  True  True  True
2014-02-15              Lớp đa số 0.5000 0.1476       0.1476 -0.2388 -0.2154 264034.0 4000 264034.0 False False False
2014-02-15      Recency đảo chiều 0.7274 0.2665       0.1476  0.0000  0.0000 260677.0 4000 264034.0  True False False
2014-03-01            MLP (32,16) 0.7743 0.1214       0.1480  0.0462  0.0648 283366.0 4000 254293.0  True  True  True
2014-03-01 Cây Gini sâu 4, lá 400 0.6295 0.1525       0.1480 -0.1005 -0.0793 258254.0 4000 254293.0 False False  True
2014-03-01    Naive Bayes rời rạc 0.7207 0.1176       0.1480 -0.0052  0.0094 289246.0 4000 254293.0  True  True  True
2014-03-01       Logistic one-hot 0.6849 0.1550       0.1480 -0.0435 -0.0251 254247.0 4000 254293.0 False False False
2014-03-01              Lớp đa số 0.5000 0.1480       0.1480 -0.2313 -0.2060 254293.0 4000 254293.0 False False False
2014-03-01      Recency đảo chiều 0.7191 0.2685       0.1480  0.0000  0.0000 259653.0 4000 254293.0  True False  True

## 2. Trung bình 4 mốc (tất cả mô hình, kể cả bổ sung)

                           auc   brier     ap1            Z  dk1_dat  dk2_dat  dk3_dat
model                                                                                 
MLP (32,16)             0.7513  0.1276  0.9211  288378.8864        4        4        4
kNN k=200               0.7410  0.1307  0.9189  283557.0916        4        4        4
Gradient boosting       0.7407  0.1314  0.9215  283224.0069        4        4        4
Random Forest 300       0.7235  0.1310  0.9161  288178.6584        3        4        4
Naive Bayes rời rạc     0.7199  0.1252  0.8949  291883.0973        4        4        4
Recency đảo chiều       0.7168  0.2691  0.8923  253315.2204        4        0        1
Cây Gini sâu 4, lá 400  0.6803  0.1395  0.8953  281489.6416        1        3        4
Logistic one-hot        0.6595  0.1513  0.8993  273406.1073        1        2        2
Lớp đa số               0.5000  0.1486  0.8193  269042.7812        0        0        0

## 3. MLP so với Naive Bayes theo Z từng mốc (luật chọn: Z cao hơn ở nhiều mốc hơn)

               Z_MLP      Z_NB  MLP_thang
E                                        
2013-12-15  290319.0  292046.0      False
2014-01-15  290012.0  293085.0      False
2014-02-15  289820.0  293156.0      False
2014-03-01  283366.0  289246.0      False

MLP thắng 0/4 mốc, NB thắng 4/4 mốc. Chênh lệch Z trung bình (MLP − NB) = -3504 USD (-1.20%).

## 4. Ổn định MLP theo seed (AUC, Brier, Z từng mốc, seed 0..4)

AUC:
E     2013-12-15  2014-01-15  2014-02-15  2014-03-01
seed                                                
0         0.7199      0.7357      0.7753      0.7743
1         0.7228      0.7098      0.7840      0.7784
2         0.7367      0.7694      0.7261      0.7864
3         0.6523      0.7146      0.7698      0.7597
4         0.7017      0.7363      0.7777      0.7608

Z:
E     2013-12-15  2014-01-15  2014-02-15  2014-03-01
seed                                                
0       290319.0    290012.0    289820.0    283366.0
1       291266.0    291904.0    289828.0    281951.0
2       291432.0    291626.0    284566.0    285083.0
3       280649.0    287514.0    282048.0    280463.0
4       288628.0    290479.0    289708.0    282204.0

Độ lệch chuẩn AUC theo seed (trung bình các mốc): 0.0228; Z: 2909 USD

## 5. Chấm điểm mốc 08/07/2014 (học ở 01/03/2014)

  MLP (32,16): n=18360, RiskScore trung vị 0.888, P75 0.917, tỷ lệ Cao (percentile>=75) 0.250, khách có v<c/r=100: 50.5%
  Naive Bayes rời rạc: n=18360, RiskScore trung vị 0.922, P75 0.975, tỷ lệ Cao (percentile>=75) 0.249, khách có v<c/r=100: 50.5%
  Cây Gini sâu 4, lá 400: n=18360, RiskScore trung vị 0.898, P75 0.943, tỷ lệ Cao (percentile>=75) 0.244, khách có v<c/r=100: 50.5%

Cây đối chứng học ở 01/03/2014:
```
|--- Recency <= 275.50
|   |--- Monetary <= 4640.88
|   |   |--- BikeBuyer <= 0.50
|   |   |   |--- Monetary <= 150.94
|   |   |   |   |--- class: 1
|   |   |   |--- Monetary >  150.94
|   |   |   |   |--- class: 1
|   |   |--- BikeBuyer >  0.50
|   |   |   |--- Monetary <= 1956.81
|   |   |   |   |--- class: 1
|   |   |   |--- Monetary >  1956.81
|   |   |   |   |--- class: 1
|   |--- Monetary >  4640.88
|   |   |--- Monetary <= 4960.65
|   |   |   |--- class: 1
|   |   |--- Monetary >  4960.65
|   |   |   |--- Monetary <= 6587.16
|   |   |   |   |--- class: 1
|   |   |   |--- Monetary >  6587.16
|   |   |   |   |--- class: 1
|--- Recency >  275.50
|   |--- Tenure <= 744.00
|   |   |--- Monetary <= 1684.87
|   |   |   |--- class: 0
|   |   |--- Monetary >  1684.87
|   |   |   |--- Monetary <= 2349.77
|   |   |   |   |--- class: 0
|   |   |   |--- Monetary >  2349.77
|   |   |   |   |--- class: 0
|   |--- Tenure >  744.00
|   |   |--- class: 0
```
Số lá: 11
      count   mean    p_m
leaf                     
4      6054  0.899  0.898
5       452  0.732  0.741
7      1756  0.995  0.990
8      1904  0.946  0.943
10      440  0.559  0.586
12      901  0.861  0.859
13      664  0.952  0.943
16      420  0.181  0.249
18      467  0.375  0.418
19      515  0.202  0.257
20      594  0.478  0.505

Khách tại 08/07/2014 có |TreeScore − RiskScore(MLP)| > 0,3: 3919 / 18360 (21.3%)