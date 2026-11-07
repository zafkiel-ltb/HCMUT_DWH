# Bàn giao dự án CompanyX DSS (cập nhật 07/11/2026)

File này thay cho `HANDOVER.md`, `docs/VAN_DE_CON_LAI.md` và các handover v4, v5 cũ (đã xoá, xem mục 9). Đọc hết trước khi sửa gì. Cách chạy lại xem `README.md`.

## 0. Trạng thái hiện tại

- **Báo cáo chính thức là bản LaTeX** trong `latex/`, không còn sửa Google Doc. Bản dựng `latex/main.pdf` 73 trang: trang phân công, mục lục, danh sách hình và bảng, chương 1 đến 8, tài liệu tham khảo, khai báo dùng AI. Phụ lục (bảng Nielsen 18 mục, 25 ca kiểm thử) đã bỏ ngày 07/11 theo quyết định của Bảo, bảng kiểm thử vẫn ở `docs/KET_QUA_KIEM_THU.md`, bảng Nielsen lấy lại được từ `latex/9_phu_luc.tex` trong lịch sử git.
- Biên dịch sạch: 0 lỗi, 0 tham chiếu `??`, mọi hình và bảng đều được nhắc trong thân bài, thân bài không có dấu chấm phẩy.
- App DSS chạy được với `results/cum6/dss_khach.csv`, đã chạy 25 ca kiểm thử của nhóm (21 đạt, 4 đạt có lưu ý).
- Toàn bộ đã đẩy lên GitHub ngày 07/11/2026 trong một commit duy nhất (lịch sử cũ đã gộp lại). Xem mục 7.

## 1. Người và liên kết

- Nhóm: Lương Thiên Bảo (2670198, chủ repo và chủ bản LaTeX), Phạm Nguyễn Thùy Dương (2670202), Phan Thị Hồng Nhung (2670221), Hoàng Ngọc Thủy Thương (2670234), Nguyễn Thái Ngọc Giao (2670206).
- Repo: https://github.com/zafkiel-ltb/HCMUT_DWH, nhánh `main`. Tài khoản commit là `zafkiel-ltb` của Bảo.
- Google Doc cũ (chỉ để tra lịch sử, không sửa): https://docs.google.com/document/d/18LCYtxYRWqz9Dqq9iuiSXKTlC2ND2yQOuJmVn8RZXYA/edit?tab=t.0
- Sheet góp ý của nhóm: https://docs.google.com/spreadsheets/d/1wHC62rOeidpSPszOSAVANAwuiXOznlC8Mb3QrQf6ObI/edit?gid=749991028
- Slide môn học: `tai_lieu_mon_hoc/Lecture 0-Overview.pdf` đến `Lecture 7-MSS Modeling.pdf` (chỉ trên máy). Thang điểm và quy định nộp ở Lecture 0, slide 12 đến 15.

## 2. Quy tắc bắt buộc

1. **Không bịa số liệu.** Mọi con số trong báo cáo phải truy được về `results/`, nhật ký ETL trong kho, hoặc chương trước. Không tự tính số mới mà không ghi cách tính.
2. **Không sửa tay** `latex/bang/*.tex` và `latex/IMAGE/*.png` do script sinh. Muốn đổi thì sửa `python/bao_cao/tao_bang_tex_*.py` hoặc `python/bao_cao/ve_*.py` rồi chạy lại.
3. Hằng số thiết kế chỉ ở `python/config.py`. Đổi hằng số là đổi thiết kế, phải sửa chương 5 và 6 trước.
4. Không chạy lại `python/phan_tich/cum4_huan_luyen.py` nếu không cần (ghi đè `models/*.joblib`, MLP đổi kết quả theo máy). Sau mọi lần chạy script, `git diff --stat results/cum5/*.sql results/cum6/*.sql` phải rỗng.
5. Chỉ một máy ghi điểm vào kho (`analytics.CustomerRiskScore`). Trước khi ghi, chạy `sql/VERIFY_STATE.sql`, mọi dòng phải khớp cột MongDoi.
6. Thân bài báo cáo: **không dùng dấu chấm phẩy**, không viết "bài giảng" hay "Lecture" (ghi "tài liệu môn học"), số kiểu Việt (0,837 và 18.360). Phần vượt ngoài slide ghi "ngoài nội dung môn học".
7. Chỉ trích dẫn nguồn đã đọc hoặc kiểm tra được nội dung. Không thêm nguồn cho đủ số.
8. **Chỉ commit khi Bảo đồng ý.** Không dùng `git add .`. Không thêm dòng `Co-Authored-By` nào vào commit hay PR.
9. Mật khẩu SQL Server (biến môi trường của container `companyx-sql`) không được in ra hay ghi vào file nào.
10. Trả lời Bảo bằng tiếng Việt, ngắn.

## 3. Thiết kế đã chốt (không đổi nếu nhóm không thống nhất lại)

- **Kho:** `CompanyX_DW` hình sao Kimball, 4 Dim và 2 Fact. ETL T-SQL `etl.usp_FullLoad` 11 bước, nhật ký `etl.RunLog`, `etl.StepLog`, bản ghi loại ở `etl.RejectedRow`. 44 phép kiểm sau ETL, 21 phép cho `analytics.CustomerSnapshot` (20 mốc, 196.985 dòng, vân tay trong `sql/VERIFY_STATE.sql`).
- **Nhãn:** y = 1 nếu khách không có đơn trong [T, T+90). Nhãn chỉ dùng khi T + 97 ≤ E, cửa sổ nhãn kết thúc trước 01/06/2014 (tháng 6/2014 không có đơn xe đạp).
- **Bốn fold (E ← T):** 15/12/2013 ← 01/09/2013, 15/01/2014 ← 01/10/2013, 15/02/2014 ← 01/11/2013, 01/03/2014 ← 15/11/2013. Chấm điểm ngày 08/07/2014 bằng mô hình học ở mốc 01/03/2014.
- **Mô hình:** chấm điểm bằng Naive Bayes rời rạc (Recency, Frequency, Monetary, BikeBuyer, NSub). Cây Gini (sâu 4, 400 khách mỗi lá) làm đối chứng, sinh luật IF-THEN. MLP (32,16), hồi quy logistic, Recency đảo chiều, lớp đa số để so sánh. Ngoài môn học: Random Forest, gradient boosting, kNN. Chọn theo ba điều kiện ở mục 5.1.3, hoà thì so Z. Naive Bayes thắng MLP về Z ở 4/4 fold.
- **RiskLevel Cao:** RiskPercentile ≥ 75 tính trong từng hạng ABC (ngưỡng 80%/95% Monetary). Nếu tính chung thì toàn bộ khách Cao rơi vào hạng C.
- **DSS:** EV = p·r·v − c, kịch bản cơ sở r = 10%, c = 10 USD, B = 40.000 USD. ABC, K-means k = 5 (N1 đến N5), kho quy tắc R1 đến R9 (R1, R9 tắt vì chưa có CRM), what-if, độ nhạy ±20%, tìm mục tiêu, mô phỏng Beta, bài toán cái túi theo kênh, dự báo hồi quy tuyến tính theo tháng. Giao diện Streamlit 5 màn hình.
- **Khả dụng:** không thử nghiệm người dùng (quyết định 04/11). Chỉ rà soát nội bộ theo Nielsen và chạy 25 ca kiểm thử chức năng.
- **Đặc điểm DSS:** báo cáo chỉ liệt kê 4 đặc điểm trong 14 đặc điểm của Turban mà hệ thống đáp ứng đầy đủ (mục 6.6.4), không liệt kê các đặc điểm đáp ứng một phần (quyết định 07/11).

## 4. Số liệu chính (đã đối chiếu với `results/` và kho)

| Đại lượng | Giá trị | Ở chương |
|---|---|---|
| ETL lần chạy cuối | 11 bước SUCCESS. 19.820 bản ghi khách trích ra, 18.484 khách cá nhân, 1.336 ngoài phạm vi. Kho 27.382 đơn, 59.795 dòng. 6 đơn và 75 dòng chi tiết bị loại | 3 |
| Kiểm tra chất lượng | 44/44 phép sau ETL, 21/21 phép Snapshot | 3 |
| Khách chấm điểm (08/07/2014) | 18.360 | 5, 6 |
| Khách rủi ro Cao | 4.592, tức 25,0% (A 1.285, B 646, C 2.661) | 5 |
| Cờ lệch giữa hai mô hình | 2.560 khách (13,9%) | 5 |
| Naive Bayes, trung bình 4 fold | ROC-AUC 0,720, Brier 0,125, Z 291.883 USD. MLP ROC-AUC 0,751 nhưng Z thấp hơn ở 4/4 mốc (chênh trung bình 3.504 USD). Recency đảo chiều 0,717, Brier 0,269 | 5.3.1 |
| Fold cuối 01/03/2014 | ROC-AUC 0,7207 so với Recency 0,7191. Brier 0,1176 so với 0,1480. Precision@4.000 là 89,33%. Z theo p·v 289.245,54 USD, chỉ theo v 254.292,63 USD, trần 339.886,26 USD. Ở mức Cao: precision 0,898, nền 0,820, sensitivity 0,274 | 5.3.3 |
| Nhãn 90 so với 180 ngày | 26,2% khách y = 1 mua lại trong ngày 90 đến 180. Trừ nhóm này Z cơ sở còn 205.555 USD | 5.3.4 |
| Kịch bản cơ sở | 4.000 khách, Z 292.595 USD, r hoà vốn 1,20%, r để Z đạt 100.000 USD là 4,21%. Mô phỏng 10.000 lần: Z trung bình 290.490 USD, xác suất lỗ 1,7% | 6.2, 6.5 |
| Theo kênh | 6.124 khách (R3 983, R5 5.141), chi 39.998 USD, Z 256.502 USD | 6.4 |
| Apriori, dự báo | 164 luật, 26 luật dùng làm gợi ý. MAPE tháng 4 và 5/2014: 8,2% số đơn, 15,4% doanh thu | 6.4, 6.5 |
| Giao diện | Nielsen 18 vấn đề, sửa 14 (vấn đề 18 còn lại: thông báo tiếng Anh của Streamlit). 25 ca kiểm thử: 21 đạt, 4 đạt có lưu ý | 6.6, Phụ lục |

## 5. Repo: từng thứ nằm ở đâu

### `latex/`
| File | Nội dung |
|---|---|
| `main.tex` | Preamble, thứ tự ghép: bìa, phân công, mục lục, 8 chương, `tltk` |
| `0_bia.tex`, `0_phan_cong.tex` | Bìa. Bảng thành viên và % đóng góp (cột công việc và % **để trống**, nhóm điền) |
| `1_tong_quan.tex` | Bối cảnh, mục tiêu, giải pháp tổng thể (Bảng 1, Hình 1 TikZ), phạm vi, dữ liệu |
| `2_co_so_ly_thuyet.tex` | Kho dữ liệu, OLAP, DSS, khai phá dữ liệu, RFM và ABC. Hình 3, 6, 7 vẽ TikZ |
| `3_etl.tex` | Khảo sát nguồn, kiến trúc, thiết kế kho, ETL 11 bước, Snapshot, 3.7 quản lý kho, giới hạn |
| `4_tien_xu_ly_eda.tex` | Dữ liệu sau ETL, khám phá, nhãn, chia theo thời gian, rời rạc hoá, lệch mốc |
| `5_mo_hinh.tex` | Bài toán, Z, ba điều kiện, huấn luyện, kết quả, giải thích, chấm điểm vào kho |
| `6_dss.tex` | Thiết kế DSS (6.1 đến 6.5) và hiện thực (6.6: người dùng, công nghệ, demo, 4 đặc điểm DSS, khả dụng, kiểm thử) |
| `7_danh_gia.tex` | Đánh giá kho, mô hình (so quy tắc, chỉ số theo cách DSS dùng, dư địa), DSS, hạn chế |
| `8_ket_luan.tex` | Kết luận, đóng góp, 8.2.1 kỹ thuật ngoài môn học, hướng phát triển |
| `tltk.tex` | 26 tài liệu tham khảo và mục "Khai báo sử dụng công cụ AI" |
| `bang/` | Bảng sinh tự động. Tiền tố `etl_` chương 3, không tiền tố chương 4, `m_` chương 5 và 7, `d_` chương 6 |
| `IMAGE/` | Hình. `eda_*` chương 4, `m_*` chương 5 và 7, `d_*` chương 6, `slide/` 5 hình lấy từ slide môn học, `logo_hcmut.png` |
| `tikz/` | Sơ đồ vẽ tay: `huong_tiep_can` (chương 1), `d_so_do_anh_huong`, `d_luong_quy_tac`, `d_uims` (chương 6) |

Script sinh bảng và hình, tất cả trong `python/bao_cao/` (đều đọc `results/`, không cần SQL Server trừ ghi chú):
| Chương | Script |
|---|---|
| 3 | `tao_bang_tex_etl.py` (đọc `results/doc/kiem_chung_chuong_4.html`, file này do `tao_ipynb_kiem_chung_4.py` sinh, cần kho), `ve_so_do_etl.py`, `ve_luoc_do_sao.py` |
| 4 | `tao_bang_tex_eda.py`, `ve_hinh_eda.py` |
| 5, 7 | `tao_bang_tex_mohinh.py`, `ve_hinh_mohinh.py` |
| 6 | `tao_bang_tex_dss.py`, `ve_hinh_dss.py` (ảnh màn hình lấy từ `results/doc/hinh_app/app_07_11_man_hinh_N.png`, chụp bằng `chup_man_hinh.mjs`) |

Mọi file trong `bang/` và `IMAGE/` đều được báo cáo dùng (đã bỏ các bảng và hình script sinh ra nhưng không đưa vào bài ngày 07/11).

### `sql/`
Thứ tự chạy và kết quả mong đợi từng bước ở `docs/README_THU_TU_CHAY.txt`. `4_Cum1b_Schema_DSS_DE_XUAT.sql` thêm giá vốn và 3 bảng DSS. `VERIFY_STATE.sql` kiểm vân tay kho, `RESET_SCORES.sql` xoá điểm, `RESET_DSS.sql` xoá kết quả DSS. Script ghi schema `analytics` cần `SET QUOTED_IDENTIFIER ON` (có sẵn trong file, với sqlcmd thêm cờ `-I`).

### `python/`
Ở gốc chỉ có file dùng chung và điểm vào. Mọi script trong thư mục con tự tìm `config.py` ở thư mục cha và gốc repo ở hai cấp trên, nên chạy từ bất kỳ thư mục nào cũng được.

| File | Vai trò |
|---|---|
| `config.py` | Kết nối qua biến môi trường và mọi hằng số thiết kế |
| `models_def.py` | Lớp mô hình dùng chung, cần để nạp `.joblib` (phải giữ ở gốc `python/` vì joblib tìm theo tên module) |
| `app_dss.py` | Giao diện DSS. Mặc định đọc CSV, `DSS_SOURCE=db` đọc kho |
| `requirements.txt`, `README_PYTHON.txt` | Môi trường và quy ước |

`phan_tich/` (chạy theo thứ tự, mỗi script ghi `results/<cụm>/` và tự kiểm):
| File | Vai trò |
|---|---|
| `cum3b_nhan_va_dac_trung.py` | Nhãn 90 ngày, `data/dataset.csv`, bảng mốc, fold, khoảng |
| `cum4_huan_luyen.py` | Huấn luyện và so sánh mô hình, ghi `models/` (không chạy lại) |
| `cum4b_bo_sung_chuong3.py` | Nhãn 180 ngày, tương quan, thử tập thuộc tính, hạt giống |
| `cum4c_du_dia.py` | Dư địa cải tiến (chương 7): trần, dữ liệu nguồn chưa dùng, lift |
| `cum5_cham_diem_sinh_sql.py` | Chấm điểm 08/07/2014, giải thích, sinh SQL ghi kho (cần kho) |
| `cum6_phan_tich_dss.py`, `cum6b_bo_sung_chuong3.py` | ABC, K-means, quy tắc, what-if, mô phỏng, kênh, dự báo, Apriori |

`bao_cao/`: 4 script `tao_bang_tex_*.py` và 5 script `ve_*.py` sinh bảng, hình cho báo cáo (bảng phân theo chương ở trên), `etl_nhat_ky.py` đọc nhật ký ETL từ HTML kiểm chứng, `ve_ho_so_companyx.py` vẽ biểu đồ cho `docs/ho_so_companyx/`.

`kiem_chung/`: `tao_ipynb_kiem_chung_4.py` sinh và chạy `kiem_chung_chuong_4.ipynb` trên kho (chỉ đọc), xuất `results/doc/kiem_chung_chuong_4.html`. `chup_man_hinh.mjs` chụp 5 màn hình app bằng Chrome headless. `labels_checks.py`, `models_check.py`, `extract.sql`, `dryrun_write.sql` là bộ kiểm trước cụm 3B (kết quả ở `results/chuan_hoa/`, script cũ chạy độc lập, không theo đường dẫn repo).

### `results/`
`chuan_hoa/` (kiểm trước cụm 3B), `cum3b/`, `cum4/`, `cum4b/`, `cum4c/`, `cum5/` (gồm SQL ghi điểm, bộ điểm chuẩn), `cum6/` (gồm `dss_khach.csv` app đọc), `cum6b/`, `doc/` (notebook kiểm chứng xuất HTML và 5 ảnh màn hình app).

### `docs/`
`README_THU_TU_CHAY.txt` (thứ tự SQL), `BIEN_BAN_CHUAN_HOA.md` (biên bản chuẩn hoá dữ liệu 01/11, đường dẫn `9_Chuan_hoa/` trong đó nay là `results/chuan_hoa/` và `python/kiem_chung/`), `kiem_thu_chuc_nang.docx` (25 ca do nhóm soạn), `KET_QUA_KIEM_THU.md` (kết quả chạy từng ca), `ho_so_companyx/` (hồ sơ giới thiệu công ty, LaTeX riêng).

## 6. Môi trường

- **Mac của Bảo:** `.venv` Python 3.9.6. SQL Server 2022 chạy trong Docker, container `companyx-sql`, cổng 1433, đã có `CompanyX` và `CompanyX_DW`. Mật khẩu `sa` nằm trong biến môi trường của container, không ghi ra ngoài. pdflatex từ TinyTeX: `export PATH="$HOME/Library/TinyTeX/bin/universal-darwin:$PATH"`.
- **Windows:** Python 3.9 đến 3.11, `scikit-learn==1.6.1`. Đặt venv ở đường dẫn ngắn (Windows chặn đường dẫn dài khi cài streamlit). SQL Server `.\SQLEXPRESS` với ODBC Driver 18, Windows Authentication (không đặt `SQL_USER`).
- App chạy ở http://localhost:8501, theme trong `.streamlit/config.toml`.

## 7. Việc còn lại

### Cần nhóm quyết (không tự làm)
1. **Điền bảng % đóng góp** ở `latex/0_phan_cong.tex` (môn bắt buộc, Lecture 0 slide 12 và 13). Cũng cần file danh sách riêng trong zip nộp.
2. **Khai báo công cụ hỗ trợ** trong `tltk.tex`: nhóm đọc lại bảng khai báo, xác nhận danh sách công cụ và câu chữ đúng với thực tế đã dùng, bổ sung nếu thiếu. Nhóm nên đọc lại chương 5 đến 8 và viết bằng lời mình những phần sẽ bị hỏi khi vấn đáp.
3. **Tài liệu tham khảo** (đã rà ngày 07/11): Han 3rd ed. ghi 2011 (năm phát hành, bản in ghi bản quyền 2012). Giữ cả hai bản Turban vì trích cho việc khác nhau: Turban và Aronson 2005 (14 đặc điểm, 4 thành phần, 4 kiểu phân tích, có trong danh sách tham khảo của môn) và Turban, Sharda, Delen 2011 (quyết định bán cấu trúc, pha Simon, quy hoạch, mô phỏng, phân hệ giao diện). Môn dùng bản mới hơn của sách này (Sharda, Delen, Turban 2020, bản 7), ai có bản 2020 thì đối chiếu lại các chỗ trích rồi đổi. Elmasri, Inmon, Kimball đều nằm trong danh sách tham khảo của môn và trích đúng nội dung (kiến trúc kho, bốn đặc trưng của Inmon, mô hình hoá chiều). Đã bỏ nguồn web Empire Data Systems (trang dạy SQL Server, không phải nguồn học thuật), thay bằng Han cho mô hình bông tuyết và tài liệu môn học cho hình OLAP. Đã thêm Buckinx và Van den Poel 2005 (chương 2, rời bỏ một phần trong bán lẻ không hợp đồng, RFM dự báo tốt nhất) và Neslin và cộng sự 2006 (chương 4, mô hình churn giữ độ chính xác sau ba tháng), hai câu trích chỉ nói đúng nội dung tóm tắt bài báo. Không thêm Peduzzi 1996 (về cỡ mẫu hồi quy logistic, bài không bàn) và Sharda 1988 (thí nghiệm hiệu quả DSS trong lớp học, không có chỗ dùng).
4. **Góp ý trong sheet của nhóm chưa làm:** phần OLAP thực tế ở chương 3 (Thương bổ sung), Related work survey, làm nổi bật phần bonus trong mục lục.
5. **Slide trình bày 10 phút và kịch bản demo.** Kịch bản demo có ở mục 6.6.3.
6. **Trang câu hỏi vấn đáp:** vì sao Naive Bayes mà không phải cây, vì sao phân vị trong từng hạng ABC, vì sao accuracy chỉ 0,379 ở mức Cao, vì sao nhãn 90 ngày, Z là gì, vì sao ROC-AUC chỉ ngang Recency mà vẫn dùng mô hình.
7. **Đóng gói nộp:** một zip tên `<GroupNo>_<TeamNo>_<SubmitterFullName>_<SubmitterStudentNo>.zip` gồm báo cáo PDF, danh sách thành viên kèm %, tài nguyên hệ thống (`sql/`, `python/`, `results/`, bản sao lưu kho). Người đại diện nộp lên LMS và bấm submit.

### Điểm yếu khoa học phải nói thẳng khi bị hỏi (đã viết ở chương 7, không được làm đẹp số)
- ROC-AUC Naive Bayes 0,7207 chỉ nhỉnh hơn quy tắc Recency đảo chiều 0,7191. Mô hình thắng ở chất lượng xác suất (Brier) chứ không ở thứ hạng.
- Khách y = 1 chiếm khoảng 82%, trong đó 26,2% mua lại ở ngày 90 đến 180. Nhóm Cao chỉ gấp 1,10 lần tỷ lệ nền.
- Z phụ thuộc r = 10% là giả định chưa đo. Chọn khách chỉ theo giá trị đã đạt 254.293 USD, mô hình thêm 13,7%.
- Cây Gini (thầy yêu cầu) chỉ làm đối chứng vì ROC-AUC 0,680.
- Dữ liệu kết thúc 30/06/2014 nên không có nhãn thật sau mốc 08/07/2014, không kiểm chứng ngoài mẫu được.

### Việc kỹ thuật nhỏ, làm khi rảnh
- Còn khoảng 13 bảng dùng `\resizebox` co chữ nhẹ (0,79 đến 1,2 lần).
- Mục 6.3.2 (K-means) còn lặp các bước đã nêu ở 6.1.
- Thông báo lỗi tiếng Anh của Streamlit ở ô nhập mã khách (Nielsen mục 18) chưa xử lý.
- `python/app_dss.py` còn số bảng cũ của Google Doc trong docstring (dòng 2 và chú thích gần dòng 546), không hiện ra giao diện.

### Commit
Ngày 07/11/2026 toàn bộ repo được gộp thành một commit mới trên `main` và đẩy lên GitHub (lịch sử trước đó đã bỏ). Từ đây mỗi lần sửa chỉ commit theo quy tắc ở mục 2: thêm file bằng tên, không `git add .`, không dòng `Co-Authored-By`, tác giả `zafkiel-ltb`.

## 8. Những gì đã kiểm (để không làm lại)

- Chương 1 đến 8: mọi số lớn truy được về `results/`, kho `CompanyX_DW` hoặc CSDL nguồn. ROC-AUC, Brier, Z, ma trận nhầm lẫn (tính lại độc lập từ `data/dataset.csv`), 26,2%, ABC, K-means, Apriori, what-if, kênh, dự báo đều khớp. Chỉ một số sửa khi rà: trung vị Monetary nhóm mua xe đạp 2.783,46.
- Mọi mục trong `tltk.tex` đều được trích ít nhất một lần, mọi `\cite` có mục tương ứng. Đã tra web: Lemmens và Gupta 2020, Flores và Whybark 1986, Nielsen 1994.
- Bố cục: 0 overfull trên 10pt, không trang thưa, không hình hay bảng bị đẩy xa chỗ nhắc. Chương 1 và 2 không còn cảnh báo.
- Bảng Nielsen đối chiếu với giao diện hiện tại ngày 07/11. 25 ca kiểm thử chạy trên app thật ngày 07/11, TC25 kiểm trực tiếp trên kho.
- Script `ve_hinh_mohinh.py` sau khi bỏ hai hình không dùng vẫn sinh ra các hình còn lại giống hệt (so md5).
- Sau khi gom script vào thư mục con (07/11): 7 script `phan_tich/` nạp được `config`, `models_def` và trỏ đúng gốc repo. 10 script `bao_cao/` chạy lại từ chỗ mới, 76 file trong `latex/bang/`, `latex/IMAGE/`, `docs/ho_so_companyx/IMAGE/` giống hệt trước khi chuyển (so md5). Các script `cum*` và notebook chưa chạy lại toàn bộ vì cần kho và mất thời gian, chỉ kiểm phần đường dẫn.

## 9. Tư liệu cũ

Mọi tư liệu thời viết trên Google Doc (handover cũ, nháp HTML, zip, bản dựng PDF cũ) và báo cáo mẫu của nhóm khác đã xoá khỏi máy ngày 07/11. Phần từng được theo dõi (HANDOVER.md, nháp trong `docs/`, HTML trong `results/doc/`) vẫn lấy lại được từ lịch sử git trước commit kế tiếp. Google Doc gốc vẫn còn trên mạng (mục 1).
