# Kết quả chạy thử 25 ca kiểm thử (file `docs/kiem_thu_chuc_nang.docx`)

Chạy ngày 07/11/2026 trên bản demo `python/app_dss.py` (Streamlit, cổng 8501), mốc 08/07/2014, mô hình Naive Bayes, thao tác qua giao diện. Số kỳ vọng cũng được đối chiếu với `results/cum6/dss_khach.csv` và `bang_4_4_*.csv`.

Lần chạy đầu: 18 đạt, 4 đạt có lưu ý, 2 không đạt (TC16, TC23), 1 chưa chạy. Sau đó đã sửa app cho TC16 (thêm cảnh báo R2 ở màn hình 4, `python/app_dss.py`) và chạy lại: đạt. TC23 đổi kỳ vọng theo thiết kế hiện tại. Kết quả cuối trong báo cáo (mục 6.6.6, Bảng 49): 21 đạt, 4 đạt có lưu ý (TC25 đã chạy sau đó).

| Ca | Kết quả | Quan sát thực tế |
|---|---|---|
| TC01 | Đạt | 18.360 khách, 4.592 mức Cao (25,0%) |
| TC02 | Đạt | Hạng A: 5.137 khách, 1.285 mức Cao. Lưu ý: các nút lọc mặc định bật hết; muốn lọc phải tắt B và C, bấm vào nút đang bật là bỏ chọn |
| TC03 | Đạt | A và N1: 4.280 khách (số này khớp `dss_khach.csv`; chưa so với số in trong bảng của báo cáo) |
| TC04 | Đạt | A và B: 7.718 khách, 1.931 mức Cao, 25,0% |
| TC05 | Đạt | 26339: 0,963; TreeScore 0,586; Cao; lá 5; hiện khối "Cần xem xét thêm" (cờ lệch) |
| TC06 | Đạt | 26774: 0,049; Thấp; lá 8; "Hai mô hình thống nhất" |
| TC07 | Đạt có lưu ý | Mã nằm trong khoảng 11000 đến 29483 nhưng không có trong dữ liệu (ví dụ 11136): "Không tìm thấy, không có khách này tại mốc chấm điểm". Mã ngoài khoảng hoặc có chữ bị ô số từ chối bằng thông báo tiếng Anh của Streamlit ("Value must be greater than or equal to 11000"), giá trị không được áp dụng, không có lỗi hệ thống |
| TC08 | Đạt | 4.000 khách, 40.000 USD, Z 292.595, r hiển thị 10% |
| TC09 | Đạt | B = 100.000: 8.554 khách, 85.540 USD, Z 386.235 |
| TC10 | Đạt | r = 20%: vẫn 4.000 khách, Z 625.189 (chưa so từng mã trong danh sách, chỉ so số khách) |
| TC11 | Đạt | Z* = 0 cho r* 1,20%; Z* = 100.000 cho r* 4,21% |
| TC12 | Đạt có lưu ý | Lưu: có thông báo "Đã lưu kịch bản vào bảng so sánh" và dòng trong bảng. Nút xoá tên "Xoá các kịch bản đã lưu" xoá tất cả kịch bản đã lưu, không xoá riêng kịch bản vừa lưu, và không có thông báo khi xoá |
| TC13 | Đạt | Ô "chi phí theo kênh" bật sẵn: 6.124 khách, chi phí 39.998, Z 256.502; R3 983, R5 5.141 (R4 không hiện vì 0 khách) |
| TC14 | Đạt | Bớt 26339 kèm lý do: 6.123 khách, Z 256.394, nhật ký có một dòng kèm lý do |
| TC15 | Đạt có lưu ý | Bớt không ghi lý do: hiện khối "Chưa có lý do điều chỉnh" và nút xuất CSV bị khoá. Không có bước "xác nhận" như file mô tả |
| TC16 | Không đạt lần đầu, đạt sau khi sửa app | Thêm 12201 (giá trị kỳ vọng âm, −2,41 USD): không có cảnh báo vi phạm R2. Chỉ có Z giảm 2,4 và chi phí lên 40.001 nên hiện "Vượt ngân sách". Cảnh báo R2 chỉ có ở màn hình 2 |
| TC17 | Đạt | Thêm 14141 (giá trị kỳ vọng +70,8): chi phí 40.023, tô đỏ "Vượt ngân sách 40.000 USD" |
| TC18 | Đạt | Mã đã có: "26339 (đã có trong danh sách)". Mã không có: "11136 (không có mã khách này)". Danh sách không đổi (6.124, Z 256.502) |
| TC19 | Đạt có lưu ý | Bắt giữ nội dung CSV (không tải file xuống): 6.124 dòng dữ liệu, gồm 6.123 khách và 1 dòng "Bớt thủ công (không chăm sóc)". Tiếng Việt đúng, có cột LyDoDieuChinh. Kỳ vọng "6.123 dòng" trong file Word không khớp |
| TC20 | Đạt | Chọn Quản lý: mở màn hình 1, có nút xuất CSV (màn hình 4) và mục đề xuất quy tắc (màn hình 5, tab "Phiên bản & quy tắc") |
| TC21 | Đạt | Phân tích dữ liệu: mở màn hình 5; màn hình 4 không có nút xuất CSV, có dòng "chỉ xem". Vai trò này vẫn thấy mục đề xuất quy tắc |
| TC22 | Đạt | Chăm sóc khách hàng: mở màn hình 4, có nút xuất CSV, không có mục đề xuất quy tắc ở cả 5 tab của màn hình 5 |
| TC23 | Không khớp mô tả cũ; trong báo cáo đã đổi kỳ vọng và ghi là đạt | Không có chữ "chưa đủ nhãn" và không có thẻ hiệu năng riêng cho mốc 08/07/2014. Màn hình 5 hiển thị ROC-AUC ở bốn mốc đã đủ nhãn, Naive Bayes ghi "đang dùng" và tô đậm. Không có "nan" ở cả 5 tab |
| TC24 | Đạt | "Gửi duyệt": hiện "Đã ghi nhận đề xuất", quy tắc ở trạng thái chờ duyệt, chưa lưu vào kho |
| TC25 | Đạt | Truy vấn trong container `companyx-sql`: `analytics.CustomerRiskScore`, ScoreDate 2014-07-08, phiên bản `NB_T20140301_v1`: 18.360 khách, 4.592 mức Cao, khớp màn hình 1 |

```sql
SELECT COUNT(*) FROM analytics.CustomerRiskScore
WHERE ScoreDate = '2014-07-08' AND RiskLevel = N'Cao';   -- kỳ vọng 4.592; thêm điều kiện phiên bản mô hình đang dùng (cột tên theo schema)
```

## Việc cần sửa để file Word khớp app

1. TC16: sửa app (thêm cảnh báo R2 khi thêm khách có giá trị kỳ vọng ≤ 0 ở màn hình 4) hoặc sửa kỳ vọng thành "chỉ báo vượt ngân sách".
2. TC19: sửa kỳ vọng thành "6.123 khách cộng 1 dòng khách bị bớt".
3. TC23: bỏ ý "chưa đủ nhãn" hoặc thêm thẻ hiệu năng ở mốc chấm điểm.
4. TC12, TC15: chỉnh lời mô tả cho đúng hành vi thật.
5. TC07, TC02: ghi rõ cách thao tác.
6. Đổi số mục (6.6.x thành 6.5.x) và số bảng sang `\ref`.
