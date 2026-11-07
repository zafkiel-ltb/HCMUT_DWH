COMPANYX - CUM 2: ETL & DATA QUALITY - HUONG DAN THUC HIEN
==========================================================
PHAM VI
- CSDL nguon CompanyX: chi doc, KHONG sua.
- CSDL CompanyX_DW: giu nguyen 4 Dim, 2 Fact ve cau truc, da hoan thanh Cum 1.
- Cum 2 sua etl.usp_FullLoad, bo sung thong tin stg.ProductRaw.ListPrice,
  stg.OrderLineRaw.SpecialOfferID, va kiem tra du lieu staging toan pham vi.
- Khong tinh lai analytics.CustomerSnapshot trong Cum 2: de Cum 3 thuc hien.
- KHONG chay create_6_tables(1).sql, 01_ETL_setup(1).sql, 02_RFM_snapshots(1).sql,
  03_run_etl(1).py trong lan nang cap nay.

BUOC 0 - BAC BUOC: BACKUP
SSMS -> Databases -> CompanyX_DW -> Tasks -> Back Up -> Full -> OK.
Da thuc hien buoc nay truoc Cum 1? Khuyen nghi backup moi lan nua truoc Cum 2.
Dung dong ETL, ML va cac thao tac thay doi DW khac tren database nay.

BUOC 1 - SSMS: C2_00_Preflight_READ_ONLY.sql
  1. Open script, Execute (F5). Xac nhan target=CompanyX_DW.
  2. Xac nhan etl.RejectedRow.IsInScope = READY.
  3. Kiem tra CompanyX.Sales.SpecialOffer.SpecialOfferID=1 la No Discount
     (hoac uu dai khong giam gia). Neu KHONG dung, dung lai xem lai quy tac.
  4. Danh sach 43677..43682 co the xuat hien trong query ve SubTotal/UnitPrice,
     nhung KHONG tu dong khang dinh co dung 6 ban ghi loi.

BUOC 2 - SSMS: C2_01_Update_ETL_Procedure.sql
  1. Open -> Execute (F5), phai thay "CLUSTER2_PROCEDURE_UPDATED".
  2. Script nay KHONG chay ETL; chi update stored procedure & staging columns.
  3. Neu loi, dung lai, KHONG chay Buoc 3.

BUOC 3 - WINDOWS CMD/Powershell: C2_02_Run_ETL_ONLY.py
  1. Khoi tao moi truong: py -m pip install pyodbc
  2. Vao thu muc da giai nen, mo CMD trong thu muc:
        py C2_02_Run_ETL_ONLY.py
     Neu SQL Server khong phai localhost:
        set SQL_SERVER=YOUR_SERVER_NAME
        py C2_02_Run_ETL_ONLY.py
  3. Phai hien "Run status: SUCCESS". Luu file C2_ETL_steps_*.csv.
  4. Runner nay KHONG goi etl.usp_RebuildSnapshots (tranh tai tao snapshot cu).

BUOC 4 - SSMS: C2_03_Verify_and_Quality.sql
  1. Open -> Execute (F5).
  2. Script thuc hien 44 phep kiem tra PASS/FAIL cho Cum 2. 44 la tong so
     CHECKS trong script moi; KHONG tu dong thay 37/37 cu cho den khi chay.
  3. Neu co FAIL, kiem tra FailedCount va khong cap nhat bao cao la PASS.
  4. Chup ket qua: Summary, Group Summary, StepLog, Rejected by IsInScope,
     va 6 ma don 43677-43682.
  5. Trong StepLog, RejectedRows chi la loi TRONG pham vi; ngoai pham vi
     du bi loi van tinh la ExcludedRows. RejectedRow log ghi NHIEU hon.
     Do do khong co viec Source=Loaded+Excluded+TongRejectedRowAllScopes.

KET QUA BAN GIAO
- C2_01...sql: procedure etl.usp_FullLoad da cap nhat.
- C2_03...sql: bang PASS/FAIL + minh chung Anh man hinh.
- ETL Log: RunID, SourceRows/LoadedRows/ExcludedRows/RejectedRows.
- RejectedRow: ghi ca IsInScope=0 va IsInScope=1.
- Xac nhan CompanyX_DW.FactSalesOrder, FactSalesOrderLine khop nguon
  da loc scope va tru loi (neu co).
- Chuyen sang Cum 3 de cap nhat Snapshot (19 moc) va tinh Tenure/Share/NSub.

GIOI HAN
- Cac script la ma
  can kiem chung tren SQL Server cua ban; khong bao dam se co dung 6 don loi.
- SpecialOfferID=1 la quy uoc tu cau truc CompanyX/AdventureWorks;
  phai xac nhan mo ta trong buoc preflight.
- 44 QA cua Cum 2 KHONG bao gom kiem tra RFM moi. Chuong 4.2.3 can ghi
  dung pham vi; kiem tra RFM se cap nhat va chay o Cum 3.
- Kich ban ETL chi tac dong CompanyX_DW; khong duoc chay song song voi nhom.
