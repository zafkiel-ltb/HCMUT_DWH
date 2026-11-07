# Cụm 4B – Phân tích bổ sung theo lời hẹn của Chương 3

## 1. Nhãn 180 ngày tại 13 mốc có cửa sổ 180 ngày kết thúc trước 2014-06-01 (Bảng 4.3.1d)
         T  so_khach  ty_le_y90  ty_le_y180  y90_1_mua_trong_90_180  ty_le_chua_den_ky
01/06/2013      5324     0.8276      0.6012                    1205             0.2735
15/06/2013      5423     0.8256      0.5912                    1271             0.2839
01/07/2013      5536     0.8215      0.5753                    1363             0.2997
15/07/2013      5889     0.8195      0.5721                    1457             0.3019
01/08/2013      6529     0.8151      0.5757                    1563             0.2937
15/08/2013      7077     0.8026      0.5829                    1555             0.2738
01/09/2013      7705     0.7945      0.5905                    1572             0.2568
15/09/2013      8249     0.7960      0.5972                    1640             0.2498
01/10/2013      8812     0.7937      0.5985                    1720             0.2459
15/10/2013      9305     0.7933      0.6004                    1795             0.2432
01/11/2013      9898     0.7935      0.6081                    1835             0.2336
15/11/2013     10447     0.8065      0.6247                    1899             0.2254
01/12/2013     11055     0.8139      0.6343                    1986             0.2207
Trung bình: y = 1 theo nhãn 90 ngày 80.8%, theo nhãn 180 ngày 59.6%. Trong số khách y90 = 1, 26.2% có mua trong ngày 90–180 (chưa đến kỳ chứ không bỏ đi).

Xếp hạng của mô hình học theo nhãn 90 ngày khi đối chiếu với nhãn 180 ngày (Bảng 4.3.1e):
         E          T                              mo_hinh  ty_le_y90  ty_le_y180  AUC_nhan90  AUC_nhan180  AP_nhan90  AP_nhan180
2013-11-01 2013-07-15 Naive Bayes (nhãn 90 ngày, thiết kế)     0.7935      0.6081      0.6827       0.7387     0.8661      0.7534
2013-11-01 2013-07-15              Cây Gini (nhãn 90 ngày)     0.7935      0.6081      0.6115       0.6299     0.8490      0.7178
2013-11-01 2013-07-15                    Recency đảo chiều     0.7935      0.6081      0.6864       0.7446     0.8742      0.7755
2013-11-15 2013-08-01 Naive Bayes (nhãn 90 ngày, thiết kế)     0.8065      0.6247      0.6913       0.7443     0.8768      0.7761
2013-11-15 2013-08-01              Cây Gini (nhãn 90 ngày)     0.8065      0.6247      0.6731       0.6955     0.8762      0.7612
2013-11-15 2013-08-01                    Recency đảo chiều     0.8065      0.6247      0.6905       0.7588     0.8828      0.7965
2013-12-01 2013-08-15 Naive Bayes (nhãn 90 ngày, thiết kế)     0.8139      0.6343      0.7070       0.7734     0.8896      0.8073
2013-12-01 2013-08-15              Cây Gini (nhãn 90 ngày)     0.8139      0.6343      0.6734       0.7090     0.8823      0.7834
2013-12-01 2013-08-15                    Recency đảo chiều     0.8139      0.6343      0.7012       0.7733     0.8896      0.8039
Học thẳng nhãn 180 ngày: không có cặp mốc nào thoả T + 187 ≤ E và E + 180 ≤ 2014-06-01. Mốc gần nhất 01/06/2013 có 100% khách một đơn, 100% mua xe đạp, 100% NSub = 1, nên không dùng để huấn luyện.
Naive Bayes thiết kế: AUC trung bình 3 mốc 0.694 với nhãn 90 ngày, 0.752 với nhãn 180 ngày. Recency đảo chiều: 0.693 và 0.759.

## 2. Tương quan hạng Spearman giữa 11 thuộc tính, trung bình 5 mốc huấn luyện ['2013-09-01', '2013-10-01', '2013-11-01', '2013-11-15', '2014-03-01'] (Bảng 4.3.2g)
     thuoc_tinh_1      thuoc_tinh_2  rho_spearman_TB  rho_min  rho_max
      Share_Bikes         BikeBuyer            0.872    0.830    0.912
      Share_Bikes Share_Accessories           -0.869   -0.899   -0.820
          Recency          Orders90           -0.847   -0.861   -0.817
          Recency         Orders180           -0.833   -0.862   -0.810
         Monetary         BikeBuyer            0.809    0.728    0.862
         Monetary            Tenure            0.755    0.701    0.780
Share_Accessories         BikeBuyer           -0.755   -0.761   -0.743
           Tenure       Share_Bikes            0.717    0.677    0.748
          Recency            Tenure            0.699    0.538    0.785
        Orders180       Share_Bikes           -0.688   -0.795   -0.331
         Monetary       Share_Bikes            0.687    0.551    0.817
         Orders90         Orders180            0.685    0.547    0.805
          Recency       Share_Bikes            0.680    0.360    0.808
           Tenure         BikeBuyer            0.673    0.598    0.707
        Orders180 Share_Accessories            0.615    0.286    0.709
Cặp |ρ| ≥ 0,7: 8. Share_Bikes–BikeBuyer 0.87; Share_Bikes–Share_Accessories -0.87; Recency–Orders90 -0.85; Recency–Orders180 -0.83; Monetary–BikeBuyer 0.81; Monetary–Tenure 0.76; Share_Accessories–BikeBuyer -0.76; Tenure–Share_Bikes 0.72

Cramér V giữa 5 thuộc tính rời rạc của Naive Bayes tại 2014-03-01 (toàn bộ, trong lớp y = 1, trong lớp y = 0):
thuoc_tinh_1 thuoc_tinh_2  V_toan_bo  V_trong_y1  V_trong_y0
    Monetary    BikeBuyer      0.923       0.912       0.982
   Frequency         NSub      0.521       0.491       0.689
   Frequency     Monetary      0.471       0.506       0.418
     Recency    BikeBuyer      0.381       0.251       0.685
   Frequency    BikeBuyer      0.333       0.418       0.180
    Monetary         NSub      0.331       0.359       0.393
     Recency     Monetary      0.320       0.218       0.512
     Recency         NSub      0.318       0.223       0.444
   BikeBuyer         NSub      0.243       0.331       0.391
     Recency    Frequency      0.220       0.160       0.443

## 3. Naive Bayes theo tập thuộc tính, trung bình 4 fold Bảng 3.12 (Bảng 4.3.2h)
                               tap    AUC  Brier     AP           Z  DK1  DK2  DK3  chenh_Z_so_thiet_ke  so_fold_Z_hon_thiet_ke  chenh_Z_lon_nhat_giua_fold
Thiết kế: R, F, M, BikeBuyer, NSub 0.7199 0.1252 0.8949 291883.0973    4    4    4               0.0000                       0                      0.0000
                           Bỏ NSub 0.7005 0.1326 0.8888 289305.9263    0    4    4           -2577.1711                       0                   5248.0636
                      Bỏ BikeBuyer 0.7289 0.1237 0.8987 291052.7098    4    4    4            -830.3876                       1                   2652.0520
                      Bỏ Frequency 0.7249 0.1245 0.8967 291339.7590    4    4    4            -543.3383                       2                   4413.9953
                       Bỏ Monetary 0.7221 0.1235 0.8918 289869.0027    4    4    4           -2014.0946                       2                   5827.7266
                       Chỉ R, F, M 0.7083 0.1312 0.8920 287456.8275    2    4    4           -4426.2698                       0                   6153.8250
          Thêm Tenure (tứ phân vị) 0.7323 0.1305 0.9004 283790.5919    4    4    4           -8092.5054                       1                  18738.9025
        Thêm Orders180 (0, 1, ≥ 2) 0.7272 0.1366 0.8993 280667.6892    4    4    4          -11215.4082                       0                  19579.9431
Kiểm tra: biến thể thiết kế khớp cụm 4 (AUC 0.7199, Z 291,883).

Độ quan trọng Gini của cây đối chứng học ở 01/03/2014:
       thuoc_tinh  do_quan_trong_Gini
          Recency              0.8305
         Monetary              0.1165
           Tenure              0.0302
        BikeBuyer              0.0228
        Frequency              0.0000
         Orders90              0.0000
        Orders180              0.0000
      Share_Bikes              0.0000
Share_Accessories              0.0000
   Share_Clothing              0.0000
             NSub              0.0000

Thời gian chạy: 33 giây.