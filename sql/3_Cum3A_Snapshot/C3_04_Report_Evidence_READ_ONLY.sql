/* C3-04 | Read-only reporting evidence; run after successful C3-03 QA */
USE [CompanyX_DW];
GO
SET NOCOUNT ON;
/* BANG 4.2 - copy all 20 rows, after checking C3-03 Failed=0 */
SELECT ROW_NUMBER() OVER (ORDER BY SnapshotDate) AS [No],
       CONVERT(CHAR(10),SnapshotDate,103) AS [MocPhanTich],
       COUNT(*) AS [SoKhachHangCoLichSuMua],
       CASE WHEN SnapshotDate='20140708' THEN N'DSS' ELSE N'Lich su' END AS [LoaiMoc]
FROM analytics.CustomerSnapshot
GROUP BY SnapshotDate ORDER BY SnapshotDate;
/* FIGURE: representative details of the 5 added features */
SELECT TOP (15) SnapshotDate,CustomerID,RecencyDays,Frequency,Monetary,
       OrdersLast90Days,OrdersLast180Days,Tenure,
       Share_Bikes,Share_Accessories,Share_Clothing,NSub
FROM analytics.CustomerSnapshot
WHERE SnapshotDate='20140708'
ORDER BY CustomerID;
/* Optional overview, COUNT is not the count of distinct customers across dates */
SELECT COUNT_BIG(*) AS TotalSnapshotRows,COUNT(DISTINCT SnapshotDate) AS NumberOfDates,
       SUM(CASE WHEN Tenure IS NULL OR Share_Bikes IS NULL
                      OR Share_Accessories IS NULL OR Share_Clothing IS NULL OR NSub IS NULL
                THEN 1 ELSE 0 END) AS IncompleteFeatureRows
FROM analytics.CustomerSnapshot;
GO
