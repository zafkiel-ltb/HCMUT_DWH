# Kiểm định dữ liệu đặc trưng và nhãn (từ CompanyX_DW)

Đơn trong kho: 27382, dòng: 59795, ngày đặt cuối: 2014-06-30, ngày gửi cuối: 2014-07-07
Snapshot trong kho: 196985 dòng, 20 mốc

## 1. Đối chiếu Snapshot kho với tính lại độc lập (Python, từ FactSalesOrder/Line)

Khoá (CustomerID, T) lệch: 0; giá trị lệch (10 cột, dung sai 0,005 tiền / 1e-5 tỷ trọng): 0

## 2. Số khách, nhãn y = 1 (không mua lại trong [T, T+90)), và đại lượng theo dõi Bảng 3.13 theo mốc

         T  khach    y1  ty_le_y1  nhan_du  mot_don   bike  nsub2  khoa_lech  gia_tri_lech
2013-06-01   5324  4406    0.8276     True   1.0000 1.0000 0.0000          0             0
2013-06-15   5423  4477    0.8256     True   0.9829 1.0000 0.0232          0             0
2013-07-01   5536  4548    0.8215     True   0.9565 1.0000 0.0652          0             0
2013-07-15   5889  4826    0.8195     True   0.9345 0.9528 0.1194          0             0
2013-08-01   6529  5322    0.8151     True   0.9110 0.8767 0.1907          0             0
2013-08-15   7077  5680    0.8026     True   0.8952 0.8238 0.2432          0             0
2013-09-01   7705  6122    0.7945     True   0.8707 0.7721 0.3002          0             0
2013-09-15   8249  6566    0.7960     True   0.8563 0.7343 0.3396          0             0
2013-10-01   8812  6994    0.7937     True   0.8424 0.7020 0.3793          0             0
2013-10-15   9305  7382    0.7933     True   0.8277 0.6761 0.4088          0             0
2013-11-01   9898  7854    0.7935     True   0.8104 0.6516 0.4452          0             0
2013-11-15  10447  8425    0.8065     True   0.7913 0.6342 0.4808          0             0
2013-12-01  11055  8998    0.8139     True   0.7711 0.6171 0.5175          0             0
2013-12-15  11564  9463    0.8183     True   0.7582 0.6024 0.5422          0             0
2014-01-01  12134  9898    0.8157     True   0.7422 0.5853 0.5668          0             0
2014-01-15  12617 10322    0.8181     True   0.7285 0.5733 0.5889          0             0
2014-02-01  13200 10869    0.8234     True   0.7142 0.5594 0.6136          0             0
2014-02-15  13694 11245    0.8212     True   0.7040 0.5493 0.6314          0             0
2014-03-01  14167 11612    0.8197     True   0.6934 0.5408 0.6494          0             0
2014-07-08  18360 18360    1.0000    False   0.6315 0.4951 0.7563          0             0

## 3. Kiểm tra miền giá trị trên toàn bộ Snapshot kho

  PASS  Frequency >= 1: vi phạm 0
  PASS  Recency >= 1 (đơn trước T, không gồm T): vi phạm 0
  PASS  Tenure >= Recency: vi phạm 0
  PASS  Orders90 <= Orders180 <= Frequency: vi phạm 0
  PASS  Monetary > 0: vi phạm 0
  PASS  Tổng Share = 1 (±1e-5): vi phạm 0
  PASS  NSub >= 1: vi phạm 0
  PASS  Không NULL ở 5 cột mới: vi phạm 0
  PASS  Tenure == Recency khi Frequency == 1: vi phạm 0
  PASS  Tập khách mỗi mốc = khách có đơn đặt và gửi trước T: lệch 0

## 4. Lịch ghép mốc Bảng 3.12: nhãn của T phải đủ 97 ngày trước E và cửa sổ nhãn kết thúc trước 01/06/2014

  PASS  E=2013-12-15 T=2013-09-01 cửa sổ nhãn [2013-09-01, 2013-11-30) nhãn đủ ngày 2013-12-07
  PASS  E=2014-01-15 T=2013-10-01 cửa sổ nhãn [2013-10-01, 2013-12-30) nhãn đủ ngày 2014-01-06
  PASS  E=2014-02-15 T=2013-11-01 cửa sổ nhãn [2013-11-01, 2014-01-30) nhãn đủ ngày 2014-02-06
  PASS  E=2014-03-01 T=2013-11-15 cửa sổ nhãn [2013-11-15, 2014-02-13) nhãn đủ ngày 2014-02-20
  PASS  E=2014-07-08 T=2014-03-01 cửa sổ nhãn [2014-03-01, 2014-05-30) nhãn đủ ngày 2014-06-06
  Tháng 6/2014: 930 đơn, dòng Bikes = 0 (lý do kết thúc cửa sổ nhãn trước 01/06/2014)

## 5. Đối chiếu nhãn với sandbox cũ (data/snapshots.csv, label_days = 90)

  cặp (khách, mốc) chung: 196985, nhãn lệch: 0

Vân tay snapshot.csv (sha256 16 ký tự): 64857702b4c1233d