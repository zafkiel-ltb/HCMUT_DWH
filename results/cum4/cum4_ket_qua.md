# Cụm 4 – Huấn luyện và so sánh mô hình

Cấu hình: đặc trưng ['Recency', 'Frequency', 'Monetary', 'Orders90', 'Orders180', 'Tenure', 'Share_Bikes', 'Share_Accessories', 'Share_Clothing', 'BikeBuyer', 'NSub'], fold [('2013-12-15', '2013-09-01'), ('2014-01-15', '2013-10-01'), ('2014-02-15', '2013-11-01'), ('2014-03-01', '2013-11-15')], g = 0.4115, kịch bản cơ sở r = 0.1, c = 10.0, B = 40000, random_state = 0
Naive Bayes: CategoricalNB alpha = 1 trên 5 thuộc tính rời rạc Bảng 3.10. Cây: gini, depth 4, min_samples_leaf 400, m = 50. MLP: (32,16) relu adam, early_stopping, z-score fit trên mốc huấn luyện.

## 1. Kết quả theo từng fold (Bảng 4.3.2a)
               mo_hinh          E    AUC  Brier  Brier_hang_so   CI_lo   CI_hi        Z_pv         Z_v   DK1   DK2   DK3
   Naive Bayes rời rạc 2013-12-15 0.7099 0.1342         0.1492 -0.0041  0.0152 292045.5868 281431.6278  True  True  True
Cây Gini sâu 4, lá 400 2013-12-15 0.7035 0.1349         0.1492 -0.0131  0.0101 288505.1074 281431.6278  True  True  True
           MLP (32,16) 2013-12-15 0.7199 0.1337         0.1492  0.0014  0.0299 290318.5747 281431.6278  True  True  True
      Logistic one-hot 2013-12-15 0.5733 0.1666         0.1492 -0.1480 -0.1121 279838.6534 281431.6278 False False False
             Lớp đa số 2013-12-15 0.5000 0.1492         0.1492 -0.2179 -0.1924 281431.6278 281431.6278 False False False
     Recency đảo chiều 2013-12-15 0.7047 0.2724         0.1492  0.0000  0.0000 239002.2026 281431.6278  True False False
     Random Forest 300 2013-12-15 0.6825 0.1377         0.1492 -0.0364 -0.0075 290460.6023 281431.6278 False  True  True
     Gradient boosting 2013-12-15 0.7049 0.1376         0.1492 -0.0133  0.0152 290238.1315 281431.6278  True  True  True
             kNN k=200 2013-12-15 0.6968 0.1355         0.1492 -0.0211  0.0068 289940.8422 281431.6278  True  True  True
   Naive Bayes rời rạc 2014-01-15 0.7203 0.1292         0.1494 -0.0046  0.0123 293084.7630 276413.2024  True  True  True
Cây Gini sâu 4, lá 400 2014-01-15 0.6872 0.1370         0.1494 -0.0393 -0.0187 290450.4984 276413.2024 False  True  True
           MLP (32,16) 2014-01-15 0.7357 0.1328         0.1494  0.0091  0.0308 290011.6619 276413.2024  True  True  True
      Logistic one-hot 2014-01-15 0.6596 0.1474         0.1494 -0.0695 -0.0450 285311.1731 276413.2024 False  True  True
             Lớp đa số 2014-01-15 0.5000 0.1494         0.1494 -0.2286 -0.2035 276413.2024 276413.2024 False False False
     Recency đảo chiều 2014-01-15 0.7161 0.2690         0.1494  0.0000  0.0000 253928.7889 276413.2024  True False False
     Random Forest 300 2014-01-15 0.7162 0.1330         0.1494 -0.0112  0.0122 292834.9115 276413.2024  True  True  True
     Gradient boosting 2014-01-15 0.7286 0.1351         0.1494 -0.0000  0.0245 291811.2917 276413.2024  True  True  True
             kNN k=200 2014-01-15 0.7198 0.1340         0.1494 -0.0084  0.0156 291347.7640 276413.2024  True  True  True
   Naive Bayes rời rạc 2014-02-15 0.7286 0.1199         0.1476 -0.0074  0.0092 293156.4949 264033.6597  True  True  True
Cây Gini sâu 4, lá 400 2014-02-15 0.7010 0.1335         0.1476 -0.0346 -0.0185 288748.6870 264033.6597 False  True  True
           MLP (32,16) 2014-02-15 0.7753 0.1224         0.1476  0.0382  0.0581 289819.6219 264033.6597  True  True  True
      Logistic one-hot 2014-02-15 0.7201 0.1361         0.1476 -0.0160  0.0016 274227.3129 264033.6597  True  True  True
             Lớp đa số 2014-02-15 0.5000 0.1476         0.1476 -0.2388 -0.2154 264033.6597 264033.6597 False False False
     Recency đảo chiều 2014-02-15 0.7274 0.2665         0.1476  0.0000  0.0000 260677.1211 264033.6597  True False False
     Random Forest 300 2014-02-15 0.7532 0.1254         0.1476  0.0170  0.0352 288869.5576 264033.6597  True  True  True
     Gradient boosting 2014-02-15 0.7683 0.1253         0.1476  0.0303  0.0517 276742.9183 264033.6597  True  True  True
             kNN k=200 2014-02-15 0.7687 0.1274         0.1476  0.0306  0.0526 278967.7527 264033.6597  True  True  True
   Naive Bayes rời rạc 2014-03-01 0.7207 0.1176         0.1480 -0.0052  0.0094 289245.5446 254292.6349  True  True  True
Cây Gini sâu 4, lá 400 2014-03-01 0.6295 0.1525         0.1480 -0.1005 -0.0793 258254.2734 254292.6349 False False  True
           MLP (32,16) 2014-03-01 0.7743 0.1214         0.1480  0.0462  0.0648 283365.6872 254292.6349  True  True  True
      Logistic one-hot 2014-03-01 0.6849 0.1550         0.1480 -0.0435 -0.0251 254247.2899 254292.6349 False False False
             Lớp đa số 2014-03-01 0.5000 0.1480         0.1480 -0.2313 -0.2060 254292.6349 254292.6349 False False False
     Recency đảo chiều 2014-03-01 0.7191 0.2685         0.1480  0.0000  0.0000 259652.7691 254292.6349  True False  True
     Random Forest 300 2014-03-01 0.7420 0.1278         0.1480  0.0130  0.0329 280549.5624 254292.6349  True  True  True
     Gradient boosting 2014-03-01 0.7611 0.1276         0.1480  0.0304  0.0533 274103.6860 254292.6349  True  True  True
             kNN k=200 2014-03-01 0.7787 0.1261         0.1480  0.0476  0.0719 273972.0074 254292.6349  True  True  True

## 2. Trung bình 4 fold và số fold đạt từng điều kiện (Bảng 4.3.2b)
                       vai_tro                mo_hinh    AUC  Brier     AP        Z_pv  DK1  DK2  DK3         Z_v    Z_oracle
                       So sánh            MLP (32,16) 0.7513 0.1276 0.9211 288378.8864    4    4    4 269042.7812 346377.5881
Bổ sung ngoài nội dung môn học              kNN k=200 0.7410 0.1307 0.9189 283557.0916    4    4    4 269042.7812 346377.5881
Bổ sung ngoài nội dung môn học      Gradient boosting 0.7407 0.1314 0.9215 283224.0069    4    4    4 269042.7812 346377.5881
Bổ sung ngoài nội dung môn học      Random Forest 300 0.7235 0.1310 0.9161 288178.6584    3    4    4 269042.7812 346377.5881
             Mô hình chấm điểm    Naive Bayes rời rạc 0.7199 0.1252 0.8949 291883.0973    4    4    4 269042.7812 346377.5881
                   Mốc so sánh      Recency đảo chiều 0.7168 0.2691 0.8923 253315.2204    4    0    1 269042.7812 346377.5881
             Mô hình đối chứng Cây Gini sâu 4, lá 400 0.6803 0.1395 0.8953 281489.6416    1    3    4 269042.7812 346377.5881
                       So sánh       Logistic one-hot 0.6595 0.1513 0.8993 273406.1073    1    2    2 269042.7812 346377.5881
                   Mốc so sánh              Lớp đa số 0.5000 0.1486 0.8193 269042.7812    0    0    0 269042.7812 346377.5881

## 3. Luật hòa 3.4.6: Z theo mốc, Naive Bayes so với MLP
                Z_NB     Z_MLP  NB_cao_hon
E                                         
2013-12-15  292046.0  290319.0        True
2014-01-15  293085.0  290012.0        True
2014-02-15  293156.0  289820.0        True
2014-03-01  289246.0  283366.0        True
NB cao hơn ở 4/4 mốc, chênh trung bình 3504 USD (+1.22%).

## 4. So sánh cấu hình (Bảng 3.15), trung bình 4 fold
  NB, học mốc gần nhất (thiết kế)      AUC=0.7199 Brier=0.1252 Z=291,883
  NB, học một lần ở mốc đầu            AUC=0.7165 Brier=0.1308 Z=283,465
  NB, gộp mọi mốc đủ nhãn              AUC=0.7132 Brier=0.1338 Z=281,033
  Cây sâu 3                            AUC=0.6692 Brier=0.1396 Z=282,077
  Cây sâu 4 (thiết kế)                 AUC=0.6803 Brier=0.1395 Z=281,490
  Cây sâu 5                            AUC=0.6829 Brier=0.1399 Z=280,941
  Cây sâu 6                            AUC=0.6869 Brier=0.1388 Z=281,633
  Cây lá 200                           AUC=0.6760 Brier=0.1428 Z=280,081
  Cây lá 800                           AUC=0.6710 Brier=0.1408 Z=278,360
  Cây m = 0                            AUC=0.6830 Brier=0.1399 Z=281,636
  Cây m = 200                          AUC=0.6803 Brier=0.1390 Z=281,314
  MLP (16,)                            AUC=0.7080 Brier=0.1402 Z=284,725
  MLP (32,16)                          AUC=0.7513 Brier=0.1276 Z=288,379
  MLP (64,32)                          AUC=0.7405 Brier=0.1282 Z=287,443

Gốc cây và số lá qua các mốc (T, E, thuộc tính gốc, ngưỡng, số lá):
  ('2013-09-01', '2013-12-15', 'Recency', 133.5, 9)
  ('2013-10-01', '2014-01-15', 'Recency', 131.5, 10)
  ('2013-11-01', '2014-02-15', 'Recency', 159.5, 9)
  ('2013-11-15', '2014-03-01', 'Recency', 170.5, 11)

MLP theo 3 hạt giống (AUC):
E     2013-12-15  2014-01-15  2014-02-15  2014-03-01
seed                                                
0         0.7199      0.7357      0.7753      0.7743
1         0.7228      0.7098      0.7840      0.7784
2         0.7367      0.7694      0.7261      0.7864
Độ lệch chuẩn AUC theo seed, trung bình các mốc: 0.0190

## 5. Mô hình cuối học ở 2014-03-01 (π = 0.8197), chấm điểm 2014-07-08 (n = 18360)
  Ngưỡng Youden của NB trên mốc huấn luyện: 0.2835. RiskScore NB: trung vị 0.922, P25 0.803, P75 0.975
  Khách |TreeScore − RiskScore| > 0.3: 2560 (13.9%)

Cây đối chứng (luật IF-THEN):
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
Lá cây (số khách, tỷ lệ y = 1 thô, TreeScore sau m-estimate):
      count   mean  TreeScore_m50
leaf                             
4      6054  0.899          0.898
5       452  0.732          0.741
7      1756  0.995          0.990
8      1904  0.946          0.943
10      440  0.559          0.586
12      901  0.861          0.859
13      664  0.952          0.943
16      420  0.181          0.249
18      467  0.375          0.418
19      515  0.202          0.257
20      594  0.478          0.505
Đã lưu bảng xác suất có điều kiện NB: results/cum4/nb_bang_xac_suat.json

Ma trận nhầm lẫn NB tại 2014-03-01 (ngưỡng Youden 0.729 chọn trên mốc huấn luyện): TP 10477, FP 1173, FN 1135, TN 1382, accuracy 0.837, sensitivity 0.902, specificity 0.541, precision 0.899

Thời gian chạy: 45 giây. Hình: hinh_4_3_2_roc_pr.png, hinh_4_3_2_ma_tran_nham_lan.png, hinh_4_3_2_phan_bo_diem.png