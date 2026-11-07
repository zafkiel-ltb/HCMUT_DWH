CLUSTER 1 - CompanyX_DW upgrade - HƯỚNG DẪN
=============================================
1) Sao lưu CompanyX_DW bằng SSMS > Databases > CompanyX_DW > Tasks > Back Up.
2) Đảm bảo cơ sở dữ liệu CompanyX_DW đã có đủ 6 bảng Dim/Fact và đã chạy 01_ETL_setup(1).sql.
3) Chỉ chạy Cluster1_01_Upgrade_DWH.sql một lần trong SSMS (có thể chạy lại nếu cần).
4) Kiểm tra thông báo CLUSTER_1_SCHEMA_OK.
5) Chạy Cluster1_02_Verify_DWH.sql; chụp kết quả kiểm tra các cột và bảng.
6) Bàn giao schema mới cho cụm 2 và 3. KHÔNG chạy lại ETL tại bước này.

PHÂN CÔNG SAU KHI HOÀN THÀNH CỤM 1
- Cụm 2: sửa etl.usp_FullLoad trong 01_ETL_setup để INSERT IsInScope (0/1), kiểm tra toàn staging
  trước khi lọc, kiểm tra thêm giá 0 và đơn SubTotal <= 0; cập nhật QA. 6 đơn lỗi chưa xác minh
  nên không tự kết luận 6 dòng chắc chắn bị reject.
- Cụm 3: sửa etl.usp_RebuildSnapshots (02_RFM_snapshots), tính 5 cột mới và dùng 19 mốc + scoring;
  sửa 03_run_etl.py / QA cho tương thích. Hiện các cột mới là NULL có chủ ý.
- Cụm 4/5: đăng ký ModelRegistry, lưu các lá cây vào ModelTreeLeaf và ghi CustomerRiskScore khi có mô hình thực sự.

CHÚ Ý
- Không chạy lại create_6_tables(1).sql trên cơ sở dữ liệu đã xây.
- Không sửa cơ sở dữ liệu OLTP CompanyX.
- Không xoá CustomerSnapshot hoặc dữ liệu Fact ở bước này.
- Với nhiều người dùng chung SQL Server, chỉ một người chạy migration này.
- ModelVersion của CustomerRiskScore phải tồn tại trước trong ModelRegistry.
- RiskPercentile >= 75 => RiskLevel 'Cao', còn lại là 'Thấp'.
- TreeScore nullable; TopFactors là luật của cây đối chứng, không phải lời giải thích trực tiếp MLP.
- IsInScope NULL ở dòng nhật ký cũ là CHƯA PHÂN LOẠI, không phải ngoài phạm vi.
