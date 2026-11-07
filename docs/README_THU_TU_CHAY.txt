COMPANYX DSS - BO SCRIPT CHAY TU A DEN Z (phan da hoan thanh: nen, cum 1, cum 2, cum 3A)
=====================================================================================
Da kiem tra chay thong toan bo chuoi ngay 31/10/2026 tren SQL Server (container), ket qua:
ETL SUCCESS, 44/44 PASS, 6 don + 75 dong ngoai pham vi, Snapshot 196.985 dong / 20 moc, 21/21 PASS.

YEU CAU
- SQL Server co san CSDL nguon CompanyX (chi doc). Tao CSDL rong CompanyX_DW truoc khi chay.
- SSMS (hoac sqlcmd). Python 3 + pyodbc + ODBC Driver 18 chi can cho buoc 2.3 (co ban thay the bang SQL).
- Moi script chay trong CSDL CompanyX_DW, tru khi ghi chu khac. Chay dung thu tu, moi file mot lan.

THU TU CHAY
0. Nen (4.2.1, 4.2.2)
   0.1  0_Nen_DWH_ETL/00_create_6_tables.sql      -> SUCCESS: created 4 dimensions, 2 facts
   0.2  0_Nen_DWH_ETL/01_ETL_setup.sql            -> SETUP_OK
1. Cum 1 - nang cap schema (them cot Snapshot, bang ModelRegistry/ModelTreeLeaf/CustomerRiskScore, IsInScope)
   1.1  Cluster1_01_Upgrade_DWH.sql               -> CLUSTER_1_SCHEMA_OK
   1.2  Cluster1_02_Verify_DWH.sql                -> tat ca cot FOUND, 7 FK goc
2. Cum 2 - ETL moi (kiem tra toan staging truoc khi loc, 2 quy tac moi, IsInScope)
   2.1  C2_00_Preflight_READ_ONLY.sql             -> xem 6 don 43677-43682
   2.2  C2_01_Update_ETL_Procedure.sql            -> CLUSTER2_PROCEDURE_UPDATED
   2.3  C2_02_Run_ETL_ONLY.py  (hoac C2_02b_Run_ETL_sqlcmd.sql neu khong co Python)
                                                  -> Status SUCCESS, 11 buoc, Order 6 / OrderLine 75 (IsInScope 0)
   2.4  C2_03_Verify_and_Quality.sql              -> 44 PASS, 0 FAIL  (chup man hinh cho 4.2.3)
3. Cum 3A - Snapshot 20 moc, 5 dac trung moi
   3.1  C3_00_Preflight_READ_ONLY.sql             -> ExistingRiskScores phai = 0
   3.2  C3_01_Install_Snapshot_Procedure.sql      -> C3_INSTALL_OK
   3.3  C3_02_Run_Snapshot_Rebuild.sql            -> 196985 dong, 20 moc, IncompleteFeatureRows 0
   3.4  C3_03_Verify_Snapshot_Quality_READ_ONLY.sql -> 21 PASS, 0 FAIL  (chup man hinh)
   3.5  C3_04_Report_Evidence_READ_ONLY.sql       -> bang 20 moc cho Bang 4.2 + mau khach 11000-11019 cho Hinh 4.8

KHONG DUA VAO GOI (da bi thay the, chay lai se pha Snapshot moi)
- 02_RFM_snapshots.sql, 03_run_etl.py, 04_Verify.sql (goi ETL_422 cu, 4 moc)
- CompanyX_DW_423_Quality_Checks.sql (37 check cu, ghi cung 4 moc)
  Thu nghiem 31/10: chay lai 02 + 03 cu lam Snapshot con 4 moc / 39.838 dong, cot moi NULL, C3_03 bao 7 FAIL.

LUU Y KHI LAM TIEP CUM 3B, 4, 5, 6 (Python)
- Sau khi analytics.CustomerRiskScore co dong, C3_01 se tu choi rebuild Snapshot. Chot Snapshot xong roi moi cham diem.
- ModelVersion phai ton tai trong analytics.ModelRegistry truoc khi ghi ModelTreeLeaf va CustomerRiskScore.
- RiskPercentile >= 75 -> RiskLevel 'Cao', con lai 'Thap'.
- Nhan 90 ngay, fold theo Bang 3.12 (moc huan luyen cuoi 01/03/2014, cham diem 08/07/2014). Khong theo comment cu [bd]/[bm].
- Dac trung lay tu analytics.CustomerSnapshot (Bang 3.9), khong tinh lai trong Python. Nhan tinh trong Python tu FactSalesOrder + DimDate.
- Chuoi ket noi doc tu bien moi truong (SQL_SERVER, SQL_DRIVER) de chay duoc ca Windows Auth va SQL login.
