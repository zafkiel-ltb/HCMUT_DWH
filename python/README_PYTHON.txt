MÔI TRƯỜNG PYTHON CHUNG (cụm 3B, 4, 5, 6)
1) Cài:   py -m venv .venv  &&  .venv\Scripts\pip install -r requirements.txt   (Windows)
          python3 -m venv .venv && .venv/bin/pip install -r requirements.txt    (macOS)
2) Đặt biến môi trường theo chú thích đầu config.py. Không ghi mật khẩu vào mã hay vào Doc.
3) Mọi script import config.py: dùng config.connect() để lấy kết nối, dùng các hằng số thiết kế ở cuối file.
4) QUY ƯỚC: chỉ MỘT máy huấn luyện và ghi điểm vào CompanyX_DW (ModelRegistry -> ModelTreeLeaf -> CustomerRiskScore).
   Máy còn lại chỉ đọc kho. Lý do: MLP đổi kết quả theo máy/seed, hai bộ điểm sẽ lệch.
5) Trước khi ghi điểm: chạy sql/VERIFY_STATE.sql, mọi dòng phải khớp cột MongDoi.
6) Cần tính lại Snapshot sau khi đã có điểm: chạy RESET_SCORES.sql trước, rồi C3_02.
