# Cụm 6 – Phân hệ mô hình và tri thức của DSS tại mốc 2014-07-08

Khách: 18360, g = 0.4115, kịch bản cơ sở r = 0.1, c = 10.0, B = 40000
Giá trị v = g·AOV: trung vị 67.5 USD, khách có v < c/r = 100 USD: 50.5%

## 1. Phân hạng ABC (ngưỡng 80% / 95%)
     so_khach  ty_le_khach  ty_trong_M  M_trung_vi   p_TB  v_trung_vi
ABC                                                                  
A        5137        0.280        0.80    4859.514  0.749     938.416
B        2581        0.141        0.15    1918.258  0.665     493.376
C       10642        0.580        0.05      71.007  0.867      20.563

## 2. K-means trên (R, ln(1+F), ln(1+M)) z-score. Hopkins trung bình 10 lần: H = 0.004 (gần 0 → có cấu trúc cụm)
  k=2: WCSS=34456, silhouette=0.412
  k=3: WCSS=25155, silhouette=0.449
  k=4: WCSS=18690, silhouette=0.409
  k=5: WCSS=14784, silhouette=0.466
  k=6: WCSS=12020, silhouette=0.452
  k=7: WCSS=10204, silhouette=0.460
  k=8: WCSS=8517, silhouette=0.471
  k=9: WCSS=6952, silhouette=0.455
  k=10: WCSS=5878, silhouette=0.481
  Chọn k = 5. ARI với 3 khởi tạo khác: [1.0, 1.0, 1.0]. ARI với Ward (10.000 mẫu): 0.995

Hồ sơ 5 nhóm (Bảng 3.24):
      so_khach  ty_le  R_trung_vi  F_trung_binh  M_trung_vi  ty_trong_M  hang_A  hang_B  hang_C  RiskScore_TB  ty_le_Cao                               mo_ta
Nhom                                                                                                                                                        
N1        4926  0.268       170.0         2.210    4909.934       0.756    4280     645       1         0.806      0.334          Mua nhiều lần, giá trị cao
N2        3741  0.204       183.0         1.000    1297.800       0.180     561    1810    1370         0.702      0.070     Mua một lần, giá trị trung bình
N3         428  0.023       917.5         1.000    3953.988       0.043     296     102      30         0.100      0.000  Mua một lần, đã lâu không quay lại
N4        1839  0.100       100.0         2.664     117.959       0.009       0      24    1815         0.969      0.552           Mua lặp lại, giá trị thấp
N5        7426  0.404       191.0         1.000      44.178       0.013       0       0    7426         0.858      0.225           Mua một lần, giá trị thấp

## 3. Ma trận Rủi ro × Giá trị (số khách)
RiskLevel   Cao  Thấp
ABC                  
A          1285  3852
B           646  1935
C          2661  7981

Cơ cấu sản phẩm theo nhóm (Bảng 3.28):
      ty_trong_Bikes  ty_trong_Accessories  ty_trong_Clothing  ty_le_da_mua_xe  NSub_TB
Nhom                                                                                   
N1             0.986                 0.009              0.005            1.000    3.332
N2             0.962                 0.025              0.013            0.999    2.312
N3             1.000                 0.000              0.000            1.000    1.000
N4             0.000                 0.731              0.269            0.000    3.232
N5             0.000                 0.773              0.227            0.000    1.738

## 4. Luật kết hợp trên giỏ tích luỹ (N = 18360 khách, 75.6% có ≥ 2 danh mục con)
quy_tac               A                 B  support  confidence   lift  chap_nhan
     R6   Touring Bikes           Helmets   0.0569      0.4925 1.5317       True
    R6b   Touring Bikes Bottles and Cages   0.0417      0.3608 1.4723       True
     R7  Mountain Bikes           Fenders   0.0485      0.2189 1.9206       True
     R8          Gloves           Helmets   0.0371      0.4985 1.5506       True
    R8b Hydration Packs Bottles and Cages   0.0192      0.4986 2.0342       True

## 5. Kịch bản cơ sở: Z = 292,595 USD, chọn K = 4000 khách, chi phí 40,000, khách có EV > 0: 8554, khách giữ lại kỳ vọng 358.1

What-if (Bảng 3.26):
   kich_ban    r    c        B      Z    K     C  giu_lai_ky_vong  delta_Z
      Cơ sở 0.10 10.0  40000.0 292595 4000 40000            358.1        0
     r = 5% 0.05 10.0  40000.0 126297 4000 40000            179.1  -166297
    r = 20% 0.20 10.0  40000.0 625189 4000 40000            716.2   332595
  c = 5 USD 0.10  5.0  40000.0 424359 8000 40000            636.8   131764
 c = 20 USD 0.10 20.0  40000.0 152066 2000 40000            183.9  -140529
 B = 20.000 0.10 10.0  20000.0 172066 2000 20000            183.9  -120529
 B = 60.000 0.10 10.0  60000.0 359388 6000 60000            506.6    66793
B = 100.000 0.10 10.0 100000.0 386235 8554 85540            657.3    93640

Độ nhạy ±20%:
  tham_so thay_doi      Z  delta_Z  delta_pct    K
        r     +20% 359114    66519       22.7 4000
        r     −20% 226076   -66519      -22.7 4000
        p     +20% 327591    34996       12.0 4000
        p     −20% 226076   -66519      -22.7 4000
g (qua v)     +20% 359114    66519       22.7 4000
g (qua v)     −20% 226076   -66519      -22.7 4000
        c     +20% 251887   -40707      -13.9 3333
        c     −20% 342856    50262       17.2 5000
        B     +20% 326198    33604       11.5 4800
        B     −20% 251405   -41190      -14.1 3200

Tìm mục tiêu (3.25), K = 4000 cố định: r* hoà vốn = 1.20%, r* để Z = 100.000 USD = 4.21%

Bảng Z theo ngân sách × r (Bảng 3.27, danh sách chốt tại r = 10%):
     B    K  r=2%  r=10%  r=20%  gia_tri_ky_vong
 20000 2000 18413 172066 364132           164383
 40000 4000 26519 292595 625189           279291
 60000 6000 23878 359388 778775           342612
100000 8554  8815 386235 858009           367364
  Lạc quan: B = 100,000. Bi quan: B = 40,000. Giá trị kỳ vọng lớn nhất: B = 100,000

Mô phỏng r ~ Beta(2,2; 19,8), 10.000 lần: r_mean=0.099, r_P5=0.021, r_P95=0.217, Z_mean=290,490, Z_P5=29,774, Z_P50=250,727, Z_P95=683,192, P_Z_am=0.017, Z_nhan_va_r_P5=23,110, Z_nhan_va_r_P50=247,463, Z_nhan_va_r_P95=707,233, kiem_dinh_r10=292,595

Dự báo hồi quy tuyến tính (huấn luyện 01/2013–03/2014, kiểm 04–06/2014):
chi_so           du_bao_04_06_2014                   thuc_te  MAPE_04_05  MAPE_nen_04_05  lech_thang_6
     n          [1971, 1976, 2175]         [2092, 2209, 930]       0.082           0.849          1.34
   rev [1553586, 1583264, 1858895] [1776250, 1936359, 48650]       0.154           0.701         37.21

## 6. Bài toán cái túi theo kênh (Bảng 3.26a): R3 1647 khách, R4 428, R5 16285. R2 loại 9588 khách có EV ≤ 0.
  Tham lam EV/chi phí: Z = 256,502 USD, chọn 6124 khách, chi 39,998 USD, theo kênh {'R5': 5141, 'R3': 983}
  Quy hoạch nguyên (scipy milp): Z = 256,502 USD, chọn 6124 khách
  Xếp theo p·v bỏ qua chi phí kênh: Z = 239,997 USD (4284 khách) → chênh +6.9%
          so_khach  duoc_chon  chi_phi   EV_tong
KenhRule                                        
R3            1647        983  24575.0  112109.0
R4             428          0      0.0       0.0
R5           16285       5141  15423.0  144392.0
Mức khớp với mô hình giá trị kỳ vọng theo nhóm:
      so_khach  ty_le_EV_duong  duoc_chon_kenh
Nhom                                          
N1        4926           0.987            3964
N2        3741           0.916            2160
N3         428           0.626               0
N4        1839           0.000               0
N5        7426           0.000               0
  Danh sách chăm sóc kịch bản cơ sở theo kênh: 6124 khách, có sản phẩm gợi ý: 51.4%

Đã sinh: dss_khach.csv (18360 dòng), CUM6_01..04.sql, sql/RESET_DSS.sql. Mong đợi khi chạy: 5 nhóm, 9 quy tắc, 6124 khuyến nghị, Z = 256,502 USD.
Tự kiểm: đạt (mỗi khách một dòng, hạng ABC trùng cụm 5, đủ 5 nhóm, danh sách trong ngân sách, tham lam = quy hoạch nguyên).