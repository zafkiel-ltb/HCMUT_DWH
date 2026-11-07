# Biên bản chuẩn hoá trước cụm 3B / 4 — CompanyX DSS
Ngày: 01/11/2026. Môi trường: SQL Server trong container `companyx-sql` (CompanyX nguồn + CompanyX_DW đã chạy đủ cụm 0 → 3A), Python 3.9.6, scikit-learn 1.6.1, pandas 2.3.3.
Mọi script và kết quả nằm trong `9_Chuan_hoa/` (scripts_kiem_dinh, ket_qua).

## 0. Kết luận nhanh
| # | Hạng mục | Kết quả | Việc phải làm |
|---|---|---|---|
| 1 | Dữ liệu kho (Fact, Snapshot 20 mốc) | **Đạt.** Tính lại độc lập bằng Python khớp 100%, 10 kiểm tra miền PASS, nhãn khớp sandbox 196.985/196.985 | Không |
| 2 | Lịch mốc Bảng 3.12, nhãn 90 ngày | **Đạt.** 5 cặp (E, T) đều thỏa T+97 ≤ E và cửa sổ kết thúc trước 01/06/2014 | Không |
| 3 | Schema cho cụm 5 (ghi điểm) | **Đạt.** Ghi thử 18.360 điểm + registry + lá cây, mọi ràng buộc chặn đúng | Script ghi phải có `SET QUOTED_IDENTIFIER ON` |
| 4 | Schema cho cụm 6 (DSS) | **Thiếu 3 bảng + giá vốn.** Đã viết và thử `DE_XUAT_Cluster1b_Schema_DSS.sql` | Bạn phụ trách cụm 1 duyệt và chạy |
| 5 | Chọn mô hình chấm điểm (3.4.6) | **Naive Bayes thắng MLP 4/4 mốc về Z.** Theo đúng luật Chương 3 phải chọn NB | **Quyết định của nhóm** (mục 5) |
| 6 | Ổn định MLP theo seed | **Không ổn định**: AUC lệch chuẩn 0,023; seed 3 mốc 1 AUC 0,652 < Recency 0,705 | Củng cố lý do chọn NB |
| 7 | Vân tay trạng thái, sao lưu, reset | Đã có `VERIFY_STATE.sql`, `RESET_SCORES.sql`, bản .bak 12,6 MB | Bạn kia chạy VERIFY_STATE trên máy Windows |
| 8 | Môi trường Python | `python_env/` (requirements, config.py, README) | Cài trên cả hai máy |

## 1. Dữ liệu và nhãn (`ket_qua/labels_checks.md`)
- Kho: 27.382 đơn, 59.795 dòng, ngày đặt cuối 30/06/2014, ngày gửi cuối 07/07/2014. Snapshot 196.985 dòng, 20 mốc.
- Tính lại 10 đặc trưng tại 20 mốc từ FactSalesOrder/Line bằng Python (không dùng thủ tục SQL của cụm 3): **0 khoá lệch, 0 giá trị lệch** (dung sai 0,005 tiền, 1e-5 tỷ trọng).
- Kiểm tra miền: Frequency ≥ 1, Recency ≥ 1, Tenure ≥ Recency, Orders90 ≤ Orders180 ≤ Frequency, Monetary > 0, tổng Share = 1, NSub ≥ 1, không NULL, Tenure = Recency khi Frequency = 1, tập khách mỗi mốc = khách có đơn đặt **và gửi** trước T. **10/10 PASS.**
- Nhãn y(T) = 1 nếu không có đơn trong [T, T+90). So với nhãn sandbox cũ: **0 lệch**. Số khách và y=1 tại 15/12/2013 (11.564; 9.463) trùng số đã ghi trong comment [bm] của Doc.
- Tháng 6/2014: 930 đơn nhưng **0 dòng Bikes** → đúng lý do Chương 3 kết thúc cửa sổ nhãn trước 01/06/2014.
- Bảng số khách / tỷ lệ y=1 / tỷ lệ 1 đơn / BikeBuyer / NSub≥2 theo 20 mốc: `ket_qua/moc_table.csv` (dùng thẳng cho 4.3.1 và Bảng 3.13).
- g (tỷ lệ lợi nhuận gộp) tính từ ProductCostHistory tại ngày đặt trên 59.795 dòng trong phạm vi: **0,4115** (Accessories 0,626, Bikes 0,406, Clothing 0,402). Chương 3 chỉ dùng g = 40% minh họa, nên không lệch.

## 2. Schema và ghi điểm (`ket_qua/dryrun.out`)
Ghi thử trong một giao dịch rồi ROLLBACK: 3 dòng ModelRegistry (SCORING/TREE/COMPARISON), 12 lá ModelTreeLeaf, 18.360 dòng CustomerRiskScore với JSON và TopFactors dài.
- OK: kiểu dữ liệu, độ dài, percentile → RiskLevel (Cao 4.590 = 25,0%).
- OK: chặn 2 mô hình SCORING cùng active, chặn RiskLevel sai percentile, chặn ModelVersion chưa đăng ký.
- OK: truy vấn màn hình 1 (điểm ⋈ snapshot ⋈ registry active) ra đúng 18.360 dòng, một dòng mỗi khách.
- **Phát hiện:** `analytics.ModelRegistry` có filtered unique index → INSERT bằng sqlcmd mặc định lỗi 1934. SSMS và pyodbc mặc định đã ON. Mọi file .sql ghi vào analytics phải mở đầu bằng `SET QUOTED_IDENTIFIER ON; SET ANSI_NULLS ON;`.
- Sau khi có điểm, C3_01 từ chối rebuild Snapshot (đúng thiết kế). Cần tính lại: chạy `RESET_SCORES.sql` trước.

## 3. Thiếu so với Chương 3 → `DE_XUAT_Cluster1b_Schema_DSS.sql`
| Chương 3 cần | Kho hiện có | Đề xuất |
|---|---|---|
| g từ giá vốn (Bảng 3.21) | Không có cột giá vốn | Thêm `FactSalesOrderLine.UnitCost` (ProductCostHistory tại ngày đặt) và `DimProduct.StandardCost` |
| `analytics.CustomerSegment` (3.5.3) | Không có | Bảng hạng ABC + ClusterID theo (CustomerID, SnapshotDate, ClusterModelVersion) |
| `analytics.CareRule` (3.5.5) | Không có | Kho quy tắc R1–R9 theo phiên bản, kèm c_k, r_k (Bảng 3.26a) |
| `analytics.CareRecommendation` (3.5.5) | Không có | Khuyến nghị theo kịch bản, FK về CustomerRiskScore |
| `analytics.ModelTreeLeaf` | Có, nhưng Chương 3 không nêu tên | Thêm tên bảng vào Bảng 3.18 ("mô hình đối chứng lưu thành bảng các lá") |
Đã thử trên bản sao: chạy được, chạy lại không lỗi (idempotent), g trong kho = 0,4115, hash Snapshot không đổi. Chỉ thêm cột/bảng, không sửa dữ liệu cũ.

## 4. Vân tay trạng thái (`VERIFY_STATE.sql`, `ket_qua/verify_state.out`)
Tất cả khớp cột MongDoi: 6 bảng Dim/Fact, Snapshot 196.985 / 20 mốc, 81 dòng reject lần chạy mới nhất, SubTotal 29.052.549,9450, TotalDue 32.103.068,4755, SHA-256 Snapshot `0x044F3D49…CE52F`, nguồn 31.465 / 121.317 / 19.820, checksum đơn nguồn −1.956.926.310.
**Việc cho bạn kia:** chạy file này trên máy Windows. Mọi dòng khớp → hai máy cùng dữ liệu, cụm 3B trở đi chạy ở đâu cũng được.
Sao lưu: `CompanyX_DW_after_C3A_20261101.bak` (khôi phục trong 1 phút thay vì chạy lại chuỗi).

## 5. Chọn mô hình chấm điểm — ĐIỂM CẦN NHÓM QUYẾT ĐỊNH (`ket_qua/models_check.md`, `folds.csv`)
Giao thức đúng Chương 3: 4 fold Bảng 3.12, 11 đặc trưng Bảng 3.9, rời rạc hoá Bảng 3.10, z-score fit trên mốc huấn luyện, g = 0,4115, kịch bản cơ sở r = 10%, c = 10, B = 40.000.

| Mô hình | AUC TB | Brier TB | Z TB (USD) | ĐK1 (AUC ≥ Recency) | ĐK2 (Brier < hằng số) | ĐK3 (Z > chỉ theo v) |
|---|---|---|---|---|---|---|
| MLP (32,16) | **0,751** | 0,128 | 288.379 | 4/4 | 4/4 | 4/4 |
| Naive Bayes rời rạc | 0,720 | **0,125** | **291.883** | 4/4 | 4/4 | 4/4 |
| Cây Gini sâu 4, lá 400 | 0,680 | 0,140 | 281.490 | 1/4 | 3/4 | 4/4 |
| Recency đảo chiều | 0,717 | — | 253.315 | — | — | 1/4 |
| Logistic one-hot | 0,660 | 0,151 | 273.406 | 1/4 | 2/4 | 2/4 |
| (bổ sung) kNN / GBM / RF | 0,741 / 0,741 / 0,724 | | 283.557 / 283.224 / 288.179 | | | |

- Cả MLP và NB đều đạt 3 điều kiện ở **4/4 mốc**. Luật hòa của Chương 3: "chọn mô hình có Z cao hơn ở nhiều mốc hơn, hòa thì chọn mô hình đơn giản hơn". **NB có Z cao hơn MLP ở 4/4 mốc** (chênh trung bình 3.504 USD, 1,2%). Kiểm tra thêm với 5 seed của MLP: NB vẫn cao hơn MLP ở mọi seed, mọi mốc.
- MLP không ổn định theo seed: độ lệch chuẩn AUC 0,023, Z 2.909 USD. Với seed 3, mốc 15/12/2013 MLP chỉ đạt AUC 0,652, **thua Recency** (0,705) → điều kiện 1 của MLP phụ thuộc seed. NB là mô hình xác định, không có vấn đề này.
- Cây Gini đối chứng thua Recency ở 3/4 mốc (CI dưới 0). Đây là mô hình giải thích, không phải mô hình chấm điểm, nên không vi phạm luật chọn, nhưng Chương 4 phải nói thật.
- Chấm điểm 08/07/2014: 18.360 khách, 25,0% RiskLevel Cao, 50,5% khách có v < c/r = 100 USD (đúng con số sandbox). Khách có |TreeScore − RiskScore| > 0,3: **21,3%** với MLP → cờ "xem xét" sẽ bật cho 1/5 khách, ngưỡng 0,3 cần đo lại ở Chương 4 (tính cho NB khi chốt mô hình).

**Ba phương án:**
- **A (khuyến nghị): làm đúng luật, chọn Naive Bayes làm mô hình chấm điểm.** MLP chuyển thành mô hình so sánh (vẫn trong slide). Lý do thêm: xác suất NB hiệu chỉnh tốt nhất (Brier), là điều mục 3.5.2 đòi hỏi vì p nhân thẳng vào giá trị kỳ vọng; mô hình xác định, tái lập 100% trên mọi máy; đơn giản hơn. Chương 3 cần sửa chữ ở: 3.1 (gạch đầu dòng mô hình), 3.4.5 (đoạn mở đầu, Bảng 3.14, 3.15), 3.4.7 (Bảng 3.18: "tệp trọng số kèm tham số chuẩn hoá" → "bảng xác suất có điều kiện theo Bảng 3.10"), Hình 3.7 nếu ghi "MLP". Phần chuẩn hoá z-score (3.2) vẫn giữ cho mô hình so sánh.
- **B: giữ MLP, sửa luật chọn** (ví dụ ưu tiên AUC khi cả hai đạt). Không khuyến nghị: đổi luật sau khi thấy kết quả.
- **C: giữ MLP, báo cáo NB có Z cao hơn.** Tự mâu thuẫn với điều kiện (3) "là điều kiện quyết định".

## 6. Các quy ước để không quay lại từ đầu
1. Không ai chạy lại create_6_tables, 01_ETL_setup, 02_RFM, 03_run_etl cũ. Gói chuẩn là `CompanyX_DSS_AZ`.
2. Trước mỗi bước ghi vào kho: chạy `VERIFY_STATE.sql`. Sau Cluster1b, cập nhật thêm dòng kiểm tra 3 bảng mới.
3. Chỉ một máy huấn luyện và ghi điểm. Máy còn lại đọc kho. Lưu mô hình (joblib) và ghi `ArtifactPath` vào ModelRegistry.
4. Script .sql ghi vào analytics: `SET QUOTED_IDENTIFIER ON`.
5. Mọi hằng số thiết kế (mốc, bins, ngưỡng 75, 0,3, kịch bản cơ sở, kênh) lấy từ `python_env/config.py`, không gõ lại trong từng script. Muốn đổi thì sửa Doc trước.
6. Thay đổi schema sau Cluster1b (nếu có) phải đi kèm cập nhật Chương 3 (3.2 hoặc 3.4.7) trong cùng lần.

## 7. Chưa làm / ngoài phạm vi lần này
- Chưa chạy VERIFY_STATE trên máy bạn kia (cần bạn ấy chạy).
- Chưa sửa Doc (chờ quyết định mục 5).
- Phiên bản pyodbc/matplotlib/streamlit trong requirements chưa kiểm trên máy thật, chỉ pandas/numpy/scikit-learn là đã kiểm.
- Đánh giá ngưỡng cờ 0,3 và hồ sơ 5 nhóm K-means sẽ làm trong cụm 5–6.

## 8. Cập nhật 01/11/2026 (sáng) – sau khi chốt Naive Bayes
- Chương 3 đã sửa theo phương án A (10 chỗ chữ, vai trò trong Bảng 3.14, Bảng 3.15, Bảng 3.18, Bảng 3.33, Hình 3.7 vẽ lại). Kiểm tra sau sửa: 79 comment nguyên vẹn, 36 bảng, 10 hình, 0 "bài giảng".
- Cụm 3B xong: `python/cum3b_nhan_va_dac_trung.py` → `data/dataset.csv` (196.985 dòng, nhãn đủ ở 19 mốc), 3 bảng + 1 hình cho 4.3.1, tham số chuẩn hoá `models/chuan_hoa_T20140301.json`. Bản nháp văn bản: `docs/DRAFT_4_3_1.md`.
- Cụm 4 xong: `python/cum4_huan_luyen.py` (46 giây) → 6 bảng + 3 hình cho 4.3.2, mô hình cuối `models/nb_T20140301.joblib`, `tree_…`, `mlp_…`, bảng xác suất NB `results/cum4/nb_bang_xac_suat.json`. Kết quả trùng khớp mục 5 ở trên (NB 4/4 mốc). Bản nháp: `docs/DRAFT_4_3_2.md`.
- Kiểm tra thêm vì NB cho xác suất rời rạc: tại 08/07/2014 chỉ có 173 giá trị RiskScore khác nhau trên 18.360 khách, nhưng nhóm đồng điểm tại phân vị 75 chỉ 131 khách (0,7%), nên RiskLevel Cao = 24,9–25,6% tuỳ cách xếp hạng đồng điểm. Không ảnh hưởng thiết kế, cụm 5 dùng PERCENT_RANK và phá hoà theo Recency giảm dần để đúng 25,0%.
- Khách có |TreeScore − RiskScore| > 0,3 với NB: 13,9% (MLP là 21,3%). Ngưỡng 0,3 giữ được.
- Chưa làm: dán 4.3.1–4.3.2 vào Doc (phần của bạn kia, chờ duyệt), cụm 5 (ghi ModelRegistry/CustomerRiskScore), bạn kia chạy VERIFY_STATE và Cluster1b.
