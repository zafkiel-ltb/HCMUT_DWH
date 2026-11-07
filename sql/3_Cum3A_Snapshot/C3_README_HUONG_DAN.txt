COMPANYX — CUM 3 / PHAN A: CustomerSnapshot + RFM + mo rong dac trung + QA
Du kien SQL Server 2025 / SSMS, database CompanyX_DW

Cac buoc thuc hien:
0. BACKUP FULL CompanyX_DW trong SSMS (Tasks > Back Up...). Khong backup OLTP CompanyX.
1. C3_00_Preflight_READ_ONLY.sql — chay va xem 6 bang, 5 cot READY,
   Fact co day du order/line, ExistingRiskScores=0. Neu thieu cot, dung lai.
2. C3_01_Install_Snapshot_Procedure.sql — chay mot lan de cap nhat
   etl.usp_RebuildSnapshots. Script nay KHONG thay du lieu Snapshot.
   Du kien thong bao C3_INSTALL_OK.
3. C3_02_Run_Snapshot_Rebuild.sql — CHINH SUA DU LIEU Snapshot: xoa 4 moc
   khong con phu hop va xay dung 19 moc lich su + 1 moc DSS 08/07/2014.
   Tac vu nam trong TRANSACTION: loi thi ROLLBACK, bao toan Snapshot cu.
   6 bang Dim/Fact khong bi thay doi.
   Du kien C3_SNAPSHOT_REBUILD_SUCCESS; SnapshotDates=20;
   IncompleteFeatureRows=0. TotalRows chua biet truoc, KHONG doan.
4. C3_03_Verify_Snapshot_Quality_READ_ONLY.sql — QA doc lap 21 phep kiem tra
   (calendar, coverage, RFM, cac share, NSub, ngay, nulls). Can thay
   TotalChecks=21, Passed=21, Failed=0 moi duoc bao cao dat.
   Neu FAIL > 0: GUI ANH summary va result chi tiet cho nhom, KHONG
   cap nhat BANG 4.2 bang du lieu chua thong qua QA.
5. C3_04_Report_Evidence_READ_ONLY.sql — chay de lay BANG 4.2 (20 dong)
   va anh Hinh CustomerSnapshot (co RFM + Tenure + Share_* + NSub).
   Giu lai anh summary QA 21 PASS, 0 FAIL de minh chung.

Luu y thiet ke:
- 19 moc lich su: 1 va 15 hang thang tu 01/06/2013 den 01/03/2014.
  01/03/2014 chi lay ngay 1; 08/07/2014 la moc thu 20 cho DSS.
- Feature chi su dung don co OrderDate < T VA ShipDate < T. Status = 5.
- Monetary = SUM(FactSalesOrder.TotalDue), Frequency = so don,
  khong dem theo dong chi tiet. Tenure = days(T - earliest OrderDate).
- NSub = COUNT DISTINCT SubcategoryID khac NULL. Shares = LineTotal
  thuoc Bikes/Accessories/Clothing chia tong LineTotal tat ca san pham,
  bao gom Components (nen tong ba Share co the nho hon 1).
- Snapshot co PK(CustomerID,SnapshotDate), khong co cot data-version.
  Do do doan script nay THAY THE TOAN BO Snapshot trong mot transaction.
  Chua thuc hien co che luu nhieu phien ban theo source-version nhu
  mo ta ly tuong o muc 3.4.3; neu bao cao can cam ket versioning thi phai
  mo rong schema rieng truoc. Khong khang dinh da versioning.
- Khong tao 90-day churn labels, khong hoc ML, khong ghi RiskScore.
  T+97<=E va lich rolling-origin la buoc tiep theo cua Cum 3.
- C2 Quality 44/44 PASS la QA cho ETL. C3 Quality 21/21 PASS neu thuc
  su chay thanh cong, la QA Snapshot RIENG, KHONG thay the ket qua C2.
- Sau khi script C3_01 duoc install, KHONG chay lai file
  02_RFM_snapshots.sql cu, vi file do se ghi de procedure bang 4 moc cu.
