# CompanyX DSS

Bài tập lớn môn Kho dữ liệu và Hệ hỗ trợ ra quyết định (CO5113, ĐH Bách Khoa TP.HCM). Đề tài: dự đoán khách hàng cá nhân rời bỏ và hệ hỗ trợ ra quyết định giữ chân khách cho CompanyX (nhà sản xuất xe đạp, dữ liệu kiểu AdventureWorks trên SQL Server).

Người mới nhận việc đọc `BAN_GIAO.md` trước (quy tắc, thiết kế đã chốt, số liệu chính, việc còn lại).

## Sản phẩm

| Sản phẩm | Ở đâu |
|---|---|
| Báo cáo (76 trang, chương 1 đến 8, phụ lục A và B) | `latex/main.pdf`, nguồn trong `latex/` |
| Kho dữ liệu `CompanyX_DW` và ETL T-SQL | `sql/`, bản sao lưu `backup/*.bak` |
| Chuỗi phân tích (nhãn, huấn luyện, chấm điểm, DSS) | `python/phan_tich/cum*.py`, kết quả trong `results/` |
| Giao diện DSS 5 màn hình (Streamlit) | `python/app_dss.py` |
| Hồ sơ giới thiệu CompanyX | `docs/ho_so_companyx/` |

## Cấu trúc thư mục

| Thư mục | Nội dung | Lên git? |
|---|---|---|
| `latex/` | Nguồn báo cáo: `main.tex`, `0_bia` đến `9_phu_luc`, `tltk.tex`, bảng sinh tự động trong `bang/`, hình trong `IMAGE/`, sơ đồ TikZ trong `tikz/` | Có (trừ `main.pdf` và file build) |
| `sql/` | Dựng kho, ETL, Snapshot, bảng DSS, script kiểm tra và reset | Có |
| `python/` | `config.py` (kết nối và hằng số), `models_def.py`, `app_dss.py` (giao diện), và ba thư mục con: `phan_tich/` chuỗi `cum3b` → `cum4` → `cum4b` → `cum4c` → `cum5` → `cum6` → `cum6b`, `bao_cao/` script sinh bảng (`tao_bang_tex_*.py`) và hình (`ve_*.py`), `kiem_chung/` notebook kiểm chứng trên kho và script chụp màn hình | Có |
| `results/` | Bảng, hình, SQL do chuỗi phân tích sinh ra, mỗi cụm một thư mục | Có |
| `docs/` | Thứ tự chạy SQL, biên bản chuẩn hoá dữ liệu, bộ ca kiểm thử và kết quả, hồ sơ CompanyX | Có |
| `data/`, `models/`, `backup/` | Dữ liệu trích từ kho, mô hình đã học, bản sao lưu kho | Chỉ `models/*.json` |
| `tai_lieu_mon_hoc/` | Slide môn học | Không |

## Chạy lại từ đầu

1. **Kho dữ liệu.** Có CSDL nguồn `CompanyX` trên SQL Server, tạo CSDL rỗng `CompanyX_DW`, chạy các file trong `sql/` theo thứ tự ở `docs/README_THU_TU_CHAY.txt`, rồi `sql/4_Cum1b_Schema_DSS_DE_XUAT.sql`. Hoặc restore `backup/CompanyX_DW_after_C3A_20261101.bak` (đã xong tới cụm 3A). Kiểm bằng `sql/VERIFY_STATE.sql`.
2. **Môi trường Python** (3.9 đến 3.11, `scikit-learn==1.6.1` bắt buộc để nạp mô hình):
   ```bash
   python3 -m venv .venv && .venv/bin/pip install -r python/requirements.txt
   ```
   Kết nối SQL đặt qua biến môi trường, xem đầu `python/config.py`. Không ghi mật khẩu vào mã hay tài liệu.
3. **Chuỗi phân tích** (mỗi script ghi vào `results/<cụm>/` và tự kiểm):
   ```bash
   for s in cum3b_nhan_va_dac_trung cum4b_bo_sung_chuong3 cum4c_du_dia cum5_cham_diem_sinh_sql cum6_phan_tich_dss cum6b_bo_sung_chuong3; do .venv/bin/python python/phan_tich/$s.py || break; done
   ```
   Không chạy lại `cum4_huan_luyen.py` nếu không cần, vì nó ghi đè `models/*.joblib`.
4. **Giao diện DSS** (đọc `results/cum6/dss_khach.csv`, đặt `DSS_SOURCE=db` để đọc thẳng từ kho):
   ```bash
   .venv/bin/python -m streamlit run python/app_dss.py
   ```

## Biên dịch báo cáo

```bash
cd latex && pdflatex main.tex && pdflatex main.tex && pdflatex main.tex
```

Bảng trong `latex/bang/` và hình trong `latex/IMAGE/` do `python/bao_cao/tao_bang_tex_*.py` và `python/bao_cao/ve_*.py` sinh từ `results/`. Không sửa tay số liệu trong hai thư mục đó, muốn đổi thì sửa script rồi chạy lại.
