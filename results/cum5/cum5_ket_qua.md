# Cụm 5 – Chấm điểm 2014-07-08 bằng mô hình học ở 2014-03-01

Khách chấm điểm: 18360. RiskLevel Cao (phân vị 75 trong từng hạng ABC): 4592 (25.0%), theo hạng: {'Cao': {'A': 1285, 'B': 646, 'C': 2661}, 'Thấp': {'A': 3852, 'B': 1935, 'C': 7981}}. Ngưỡng RiskScore tại phân vị 75 toàn bộ: 0.9754. Cờ |TreeScore − RiskScore| > 0.3: 2560 (13.9%).

## Bảng 4.3.3a – Lớp 1: chỉ số phân lớp (Lecture 5, slide 69–70) của Naive Bayes tại mốc 2014-03-01 ở ba ngưỡng, kèm cách luôn dự đoán lớp đa số
Ngưỡng ngoài mẫu: Naive Bayes học ở 2013-08-01, dự đoán mốc 2013-11-15 (nhãn đủ trước 2014-03-01), chọn ngưỡng Youden trên dự đoán đó.
                                      Youden trên mốc huấn luyện (RiskScore ≥ 0.729)  Youden ngoài mẫu (RiskScore ≥ 0.878)  Phân vị 75 trong từng hạng ABC (RiskLevel Cao)  Luôn dự đoán y = 1 (lớp đa số)
Chỉ số                                                                                                                                                                                                    
Số khách bị cảnh báo (dự đoán y = 1)                                      11650.0000                             9125.0000                                       3544.0000                      14167.0000
Tỷ lệ khách bị cảnh báo                                                       0.8223                                0.6441                                          0.2502                          1.0000
TP                                                                        10477.0000                             8171.0000                                       3182.0000                      11612.0000
FP                                                                         1173.0000                              954.0000                                        362.0000                       2555.0000
FN                                                                         1135.0000                             3441.0000                                       8430.0000                          0.0000
TN                                                                         1382.0000                             1601.0000                                       2193.0000                          0.0000
Accuracy                                                                      0.8371                                0.6898                                          0.3794                          0.8197
Tỷ lệ lỗi                                                                     0.1629                                0.3102                                          0.6206                          0.1803
Precision                                                                     0.8993                                0.8955                                          0.8979                          0.8197
Sensitivity (recall)                                                          0.9023                                0.7037                                          0.2740                          1.0000
Specificity                                                                   0.5409                                0.6266                                          0.8583                          0.0000
F1                                                                            0.9008                                0.7881                                          0.4199                          0.9009

## Bảng 4.3.3b – Lớp 2 và Lớp 3 của Naive Bayes tại mốc 2014-03-01
                         Lớp                    Chỉ số  Giá trị tại mốc 2014-03-01
Lớp 2 – xếp hạng và xác suất                   ROC-AUC                      0.7207
                             ROC-AUC Recency đảo chiều                      0.7191
                                              AP lớp 1                      0.8933
                                              AP lớp 0                      0.4759
                                                 Brier                      0.1176
                                 Brier dự đoán hằng số                      0.1480
                                Precision@K (K = 4000)                      0.8932
  Lớp 3 – giá trị quyết định          Z theo p·v (USD)                 289245.5446
                                    Z chỉ theo v (USD)                 254292.6349
                               Z biết trước nhãn (USD)                 339886.2578

## Bảng 4.3.4a – Ba khách minh hoạ (rủi ro cao, có cờ lệch, rủi ro thấp)
 CustomerID  Recency  Frequency  Monetary  RiskScore  RiskPercentile RiskLevel  TreeScore  Flag                                                                                                                                                 TopFactors
      12201      180          2   64.2890   0.993339         100.000       Cao   0.897933     0 Lá 1: Recency <= 275.50 AND Monetary <= 4640.88 AND BikeBuyer <= 0.50 AND Monetary <= 150.94 | nhóm 6054 khách, tỷ lệ không mua lại 89.9%, TreeScore 0.898
      26339      186          2 4923.3161   0.962913          99.747       Cao   0.585679     1                        Lá 5: Recency <= 275.50 AND Monetary > 4640.88 AND Monetary <= 4960.65 | nhóm 440 khách, tỷ lệ không mua lại 55.9%, TreeScore 0.586
      26774      508          1  865.2040   0.049316           0.009      Thấp   0.248899     0                           Lá 8: Recency > 275.50 AND Tenure <= 744.00 AND Monetary <= 1684.87 | nhóm 420 khách, tỷ lệ không mua lại 18.1%, TreeScore 0.249

## Bảng 4.3.4b – Xác suất có điều kiện P(x | y) của Naive Bayes học ở 2014-03-01 (tỷ số > 1 làm tăng rủi ro). Tiên nghiệm P(y=1) = 0.8197
thuoc_tinh  khoang  P_x_y0  P_x_y1  ty_so
   Recency     <90  0.2038  0.3607  1.770
   Recency  90–179  0.1699  0.3494  2.057
   Recency 180–269  0.0922  0.2299  2.495
   Recency 270–364  0.1347  0.0141  0.105
   Recency 365–539  0.1316  0.0116  0.088
   Recency    ≥540  0.2679  0.0343  0.128
 Frequency       1  0.7584  0.6789  0.895
 Frequency       2  0.1994  0.2750  1.379
 Frequency      ≥3  0.0422  0.0461  1.093
  Monetary      Q1  0.1442  0.2750  1.907
  Monetary      Q2  0.1364  0.2741  2.010
  Monetary      Q3  0.4361  0.2086  0.478
  Monetary      Q4  0.2833  0.2423  0.855
 BikeBuyer       0  0.2878  0.4970  1.727
 BikeBuyer       1  0.7122  0.5030  0.706
      NSub       1  0.6604  0.2823  0.427
      NSub       2  0.1336  0.3673  2.748
      NSub     3–4  0.1661  0.3055  1.840
      NSub      ≥5  0.0399  0.0449  1.127

Đã sinh 4 file SQL trong results/cum5/. Mong đợi sau khi chạy: 18360 khách, Cao 4592 (25.0%), cờ lệch 2560.

Tự kiểm: đạt (mỗi khách một dòng, RiskLevel khớp phân vị, mỗi hạng ABC 25% Cao, ba khách minh hoạ đúng vai trò, lá cây phủ đủ khách).