Không nối CSDL nguồn ((18456, b"Login failed for user 'sa'.DB-Lib error message 20018, severity 14:\nG), dùng data/khach_nhan_khau.csv và data/don_ly_do.csv sẵn có.
# Cụm 4C – Dư địa cải tiến mô hình

Cấu hình: fold [('2013-12-15', '2013-09-01'), ('2014-01-15', '2013-10-01'), ('2014-02-15', '2013-11-01'), ('2014-03-01', '2013-11-15')], kịch bản cơ sở r = 0.1, c = 10.0, B = 40000, g = 0.4115. Gradient boosting {'max_depth': 4, 'learning_rate': 0.05, 'max_iter': 300, 'random_state': 0}, có trọng số dịch chuyển phân bố (ngoài nội dung môn học).

xong fold 2013-12-15
xong fold 2014-01-15
xong fold 2014-02-15
xong fold 2014-03-01

## 1. Dữ liệu nguồn chưa dùng: trung bình 4 fold (Bảng 7 dư địa nguồn)
                                mo_hinh    AUC  Brier        Z_pv  fold_Z_hon_NB
                    Naive Bayes rời rạc 0.7199 0.1252 291883.0973              0
GB 11 thuộc tính + trọng số dịch chuyển 0.7549 0.1291 284604.2396              0
    GB 11 + nhân khẩu học + hành vi mới 0.8110 0.1211 289916.1527              1
        Trung bình Naive Bayes và GB đủ 0.8223 0.1144 292148.9753              3

## 2. Z trung bình 4 fold theo ngân sách
B                                          20000     40000     60000     100000
mo_hinh                                                                        
Naive Bayes rời rạc                      164678.0  291883.0  354548.0  366756.0
GB 11 thuộc tính + trọng số dịch chuyển  175019.0  284604.0  352826.0  366656.0
GB 11 + nhân khẩu học + hành vi mới      181749.0  289916.0  352873.0  366571.0
Trung bình Naive Bayes và GB đủ          180656.0  292149.0  354858.0  366788.0
Chỉ theo giá trị v                       164265.0  269043.0  352074.0  347887.0
Trần khi biết nhãn                       214420.0  346378.0  382258.0  351656.0

## 3. Trần theo ô thuộc tính (trong mẫu tại mốc đánh giá), trung bình 4 fold
NB_thuc_te                   291883.1
tran_5_thuoc_tinh            293906.8
so_o_5                          116.0
tran_them_vung               300673.4
tran_them_vung_xe_thunhap    308532.1
so_o_8                         1606.0
tran_biet_nhan               346377.6

## 4. Lift theo decile của Naive Bayes tại mốc 01/03/2014
 decile  so_khach  ty_le_y1   lift  tich_luy_bat_duoc    nen
      1      1417    0.9153 1.1167             0.1117 0.8197
      2      1417    0.8885 1.0840             0.2201 0.8197
      3      1417    0.8716 1.0633             0.3265 0.8197
      4      1416    0.8919 1.0882             0.4352 0.8197
      5      1417    0.8701 1.0616             0.5414 0.8197
      6      1417    0.9499 1.1589             0.6573 0.8197
      7      1416    0.8934 1.0899             0.7663 0.8197
      8      1417    0.9083 1.1081             0.8771 0.8197
      9      1417    0.6570 0.8016             0.9573 0.8197
     10      1416    0.3503 0.4274             1.0000 0.8197

Trung bình 4 fold
 decile  so_khach  ty_le_y1   lift  tich_luy_bat_duoc    nen
      1    1301.5    0.9061 1.1059             0.1106 0.8193
      2    1301.0    0.8953 1.0927             0.2199 0.8193
      3    1301.5    0.8969 1.0947             0.3294 0.8193
      4    1300.5    0.9134 1.1149             0.4408 0.8193
      5    1301.0    0.8974 1.0953             0.5504 0.8193
      6    1301.5    0.9139 1.1154             0.6620 0.8193
      7    1300.5    0.8748 1.0677             0.7687 0.8193
      8    1301.5    0.8230 1.0043             0.8692 0.8193
      9    1301.0    0.6078 0.7419             0.9433 0.8193
     10    1300.5    0.4644 0.5669             1.0000 0.8193

## 5. AUC đơn lẻ từng đặc trưng bổ sung tại mốc 01/03/2014 (Recency để so: 0.281)
           dac_trung                                 ten   AUC
            ngoai_te                     Có đơn ngoại tệ 0.652
         TerritoryID                       Vùng bán hàng 0.645
         xe_lan_cuoi              Đơn gần nhất có xe đạp 0.605
khong_ly_do_lan_cuoi    Đơn gần nhất không ghi lý do mua 0.590
           so_don_xe                    Số đơn có xe đạp 0.553
      khoang_cach_TB Khoảng cách trung bình giữa các đơn 0.544
            thu_nhap                            Thu nhập 0.534
                nghe                         Nghề nghiệp 0.531
       xu_huong_tien      Tiền đơn gần nhất / trung bình 0.529
       TotalChildren                              Số con 0.520
             hoc_van                             Học vấn 0.519
    ty_le_khuyen_mai         Tỷ lệ đơn mua vì khuyến mãi 0.516
 khuyen_mai_lan_cuoi      Đơn gần nhất mua vì khuyến mãi 0.514
           nha_rieng                        Có nhà riêng 0.513
                 nam                       Giới tính nam 0.511
NumberChildrenAtHome                        Số con ở nhà 0.507
     ty_le_quang_cao          Tỷ lệ đơn mua vì quảng cáo 0.507
                tuoi                                Tuổi 0.505
      ngay_tu_mua_xe              Ngày từ lần mua xe đạp 0.505
             ket_hon                          Đã kết hôn 0.504
      EmailPromotion                  Đăng ký nhận email 0.503
     NumberCarsOwned                           Số xe hơi 0.503
       tung_giam_gia                  Từng được giảm giá 0.500

## Tóm tắt
{
 "AUC_NB": 0.7199,
 "AUC_GB_du": 0.811,
 "AUC_trung_binh": 0.8223,
 "Brier_NB": 0.1252,
 "Brier_trung_binh": 0.1144,
 "Z_NB": 291883,
 "Z_trung_binh": 292149,
 "Z_20000_NB": 164678,
 "Z_20000_trung_binh": 180656,
 "tran_5": 293907,
 "tran_8": 308532,
 "tran_nhan": 346378,
 "ty_le_dat_tran_5": 0.9931,
 "phan_ngau_nhien": 0.6945,
 "lift_decile1_moc_cuoi": 1.1167,
 "lift_toi_da": 1.22,
 "so_khach_nhan_khau": 18484
}

Thời gian: 6 s
