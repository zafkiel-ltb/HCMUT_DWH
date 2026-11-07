# Cụm 6B – Phân tích DSS bổ sung theo lời hẹn của Chương 3, mốc 2014-07-08


Cùng 5 luật tính theo giỏ TỪNG ĐƠN (27382 đơn): R6 sup 0.0322 conf 0.412 lift 1.77 | R6b sup 0.0199 conf 0.255 lift 1.48 | R7 sup 0.0325 conf 0.181 lift 2.35 | R8 sup 0.0218 conf 0.420 lift 1.80 | R8b sup 0.0119 conf 0.453 lift 2.63
## 1. Apriori trên 18360 giỏ danh mục con tích luỹ (đơn đặt và gửi trước 2014-07-08), 17 danh mục con, min support 1%, min confidence 20%, lift > 1
Tập phổ biến theo kích thước: {1: 17, 2: 55, 3: 48, 4: 6}. Luật đạt ngưỡng: 164 (luật 2 mục: 37, luật 3 mục: 127). Luật confidence ≥ 50%: 39.
15 luật lift cao nhất:
                                           A                                  B  so_muc  support  confidence   lift  ve_phai_phu_kien
                  Road Bikes + Touring Bikes           Helmets + Mountain Bikes       4   0.0133      0.4529 6.0338             False
             Tires and Tubes + Touring Bikes           Helmets + Mountain Bikes       4   0.0117      0.4127 5.4982             False
                  Road Bikes + Touring Bikes Bottles and Cages + Mountain Bikes       4   0.0108      0.3660 5.4675             False
Bottles and Cages + Helmets + Mountain Bikes                      Touring Bikes       4   0.0153      0.5723 4.9563             False
           Bottles and Cages + Touring Bikes           Helmets + Mountain Bikes       4   0.0153      0.3673 4.8940             False
                    Helmets + Mountain Bikes  Bottles and Cages + Touring Bikes       4   0.0153      0.2039 4.8940             False
  Helmets + Mountain Bikes + Tires and Tubes                      Touring Bikes       4   0.0117      0.5599 4.8489             False
                       Caps + Mountain Bikes                      Touring Bikes       3   0.0144      0.5248 4.5446             False
                        Fenders + Road Bikes                     Mountain Bikes       3   0.0264      1.0000 4.5166             False
                     Fenders + Touring Bikes                     Mountain Bikes       3   0.0117      1.0000 4.5166             False
                               Touring Bikes           Helmets + Mountain Bikes       3   0.0363      0.3146 4.1919             False
                    Helmets + Mountain Bikes                      Touring Bikes       3   0.0363      0.4840 4.1919             False
   Helmets + Tires and Tubes + Touring Bikes                     Mountain Bikes       4   0.0117      0.8921 4.0293             False
          Bottles and Cages + Mountain Bikes            Helmets + Touring Bikes       4   0.0153      0.2286 4.0209             False
                     Helmets + Touring Bikes Bottles and Cages + Mountain Bikes       4   0.0153      0.2692 4.0209             False

Luật dùng được làm gợi ý (1 mục mỗi vế, vế phải là phụ kiện hoặc quần áo): 26.
              A                 B  so_muc  support  confidence   lift  ve_phai_phu_kien
         Shorts              Caps       2   0.0136      0.2473 2.1548              True
         Shorts           Jerseys       2   0.0203      0.3680 2.1311              True
Hydration Packs Bottles and Cages       2   0.0192      0.4986 2.0342              True
 Mountain Bikes           Fenders       2   0.0485      0.2189 1.9206              True
    Bike Stands   Tires and Tubes       2   0.0114      0.8750 1.9100              True
           Caps           Jerseys       2   0.0370      0.3227 1.8692              True
        Jerseys              Caps       2   0.0370      0.2145 1.8692              True
         Gloves           Jerseys       2   0.0206      0.2775 1.6069              True
         Gloves           Helmets       2   0.0371      0.4985 1.5506              True
  Touring Bikes           Helmets       2   0.0569      0.4925 1.5317              True
       Cleaners Bottles and Cages       2   0.0172      0.3657 1.4922              True
  Touring Bikes Bottles and Cages       2   0.0417      0.3608 1.4723              True

Năm luật ứng viên Bảng 3.29 trong kết quả Apriori:
quy_tac               A                 B  support  confidence  lift  co_trong_ket_qua_Apriori  hang_trong_moi_luat  hang_trong_luat_goi_y  support_theo_don  confidence_theo_don  lift_theo_don
     R6   Touring Bikes           Helmets   0.0569      0.4925 1.532                      True                   94                     10            0.0322               0.4116          1.768
    R6b   Touring Bikes Bottles and Cages   0.0417      0.3608 1.472                      True                  101                     12            0.0199               0.2548          1.479
     R7  Mountain Bikes           Fenders   0.0485      0.2189 1.921                      True                   61                      4            0.0325               0.1809          2.354
     R8          Gloves           Helmets   0.0371      0.4985 1.551                      True                   89                      9            0.0218               0.4197          1.803
    R8b Hydration Packs Bottles and Cages   0.0192      0.4986 2.034                      True                   53                      3            0.0119               0.4529          2.630

## 2. Độ nhạy ngưỡng ABC (thiết kế 80%/95% so với 70%/90%)
   nguong    A    B     C  Cao_A  Cao_B  Cao_C  R3_du_dk  R3_chon  R5_chon  so_chon      Z   chi  chenh_Z  khach_doi_hang
80% / 95% 5137 2581 10642   1285    646   2661      1647      983     5141     6124 256502 39998        0               0
70% / 90% 4019 2539 11802   1005    635   2951      1499      934     5546     6480 254700 39988    -1802            2278

## 3. Quy mô nhóm không mua lại trong 90 ngày (y = 1) và phần chi tiêu liên quan, 19 mốc có nhãn
            so_khach  ty_le_y1  ty_trong_Monetary_y1  ty_trong_v_y1
T                                                                  
15/12/2013   11564.0    0.8183                0.7869         0.7552
01/01/2014   12134.0    0.8157                0.7859         0.7521
15/01/2014   12617.0    0.8181                0.7934         0.7552
01/02/2014   13200.0    0.8234                0.7995         0.7597
15/02/2014   13694.0    0.8212                0.7925         0.7477
01/03/2014   14167.0    0.8197                0.7855         0.7386
Trung bình 19 mốc: y = 1 chiếm 81.2% số khách và 78.0% tổng Monetary.

## 4. Khách quay lại trong 90 ngày: số đơn và giá trị đơn (19 mốc)
         T  khach_quay_lai  so_don_TB  ty_le_1_don  ty_le_2_don  ty_le_3_don_tro_len  gia_tri_don_quay_lai_TB  AOV_truoc_TB  ty_so_trung_vi  ty_so_tong
15/12/2013            2101     1.1290       0.9267       0.0562               0.0171                1399.4443     1660.0504          0.9720      0.8465
01/01/2014            2236     1.1199       0.9298       0.0555               0.0148                1359.0850     1591.7967          1.0084      0.8589
15/01/2014            2295     1.1203       0.9277       0.0553               0.0170                1306.9490     1545.5209          1.0146      0.8464
01/02/2014            2331     1.1184       0.9279       0.0545               0.0176                1262.6995     1509.0084          1.0143      0.8352
15/02/2014            2449     1.1111       0.9322       0.0527               0.0151                1239.1090     1525.0829          0.9888      0.8137
01/03/2014            2555     1.1041       0.9374       0.0462               0.0164                1221.0892     1529.9230          0.9536      0.7962
Trung bình có trọng số 19 mốc: 1.12 đơn mỗi khách quay lại, 93.5% chỉ một đơn. Trung vị tỷ số giá trị đơn quay lại / AOV trước: 0.87.

## 5. Tỷ lệ lợi nhuận gộp g theo nhóm sản phẩm (59795 dòng trong phạm vi)
             so_dong     doanh_thu       gia_von       g  ty_trong_doanh_thu
Category                                                                    
Accessories  35719.0  6.938910e+05  2.595164e+05  0.6260              0.0239
Bikes        15050.0  2.802152e+07  1.663709e+07  0.4063              0.9645
Clothing      9026.0  3.371428e+05  2.017902e+05  0.4015              0.0116
Toàn bộ      59795.0  2.905255e+07  1.709840e+07  0.4115              1.0000
Nếu dùng g theo nhóm thay cho g chung ở kịch bản cơ sở: Z 292,595 → 290,014 USD (-0.9%), 99.7% khách trong danh sách giữ nguyên.

## 5b. Nếu 26.2% khách "không mua lại" thực ra sẽ tự quay lại trong ngày 90–180 (không nhờ chăm sóc): Z cơ sở 292,595 → 205,555 USD, r hoà vốn 1.20% → 1.63%.
## 5c. Kênh R4 (N3) chỉ có khách được chọn khi ngân sách từ khoảng 61,213 USD trở lên (xếp theo EV trên chi phí).

## 6. Các đại lượng của mô hình giá trị kỳ vọng đo từ dữ liệu
                                                    dai_luong                           gia_tri                                                            ghi_chu muc_chuong_3
                               Tỷ lệ lợi nhuận gộp g, toàn bộ                            0,4115 Giá vốn ProductCostHistory tại ngày đặt, 59.795 dòng trong phạm vi        3.5.2
                         g của Bikes / Accessories / Clothing             0,406 / 0,626 / 0,402                                        Bikes chiếm 96,5% doanh thu        3.5.2
                        Z kịch bản cơ sở nếu dùng g theo nhóm 290.014 USD (g chung 292.595 USD)                             99,7% khách trong danh sách giữ nguyên        3.5.2
              Tỷ lệ khách không mua lại trong 90 ngày (y = 1)                             81,2%                                          Trung bình 19 mốc có nhãn        3.5.1
                            Tỷ trọng Monetary của khách y = 1                             78,0%                                          Trung bình 19 mốc có nhãn        3.5.1
           Số đơn trung bình của khách quay lại trong 90 ngày                              1,12                                              93,5% chỉ đặt một đơn        3.5.2
Giá trị đơn khi quay lại so với AOV trước đó (trung vị tỷ số)                              0,87                              Trung bình 1.427 USD so với 1.873 USD 3.5.2, 3.5.4
                 Khách có v < c/r = 100 USD tại mốc chấm điểm                             50,5%   Khách loại "B" ở mục 3.5.2: chăm sóc riêng không bù được chi phí        3.5.2
               Z cơ sở nếu trừ khách chưa đến kỳ khỏi lợi ích     205.555 USD (r hoà vốn 1,63%)   26,2% khách y = 1 theo nhãn 90 ngày tự mua lại trong ngày 90–180 3.4.1, 3.5.4
              Ngân sách để kênh R4 (nhóm N3) bắt đầu có khách                 khoảng 61.213 USD     Dưới mức này lợi trên mỗi USD của khách N3 thấp hơn khách khác        3.5.4