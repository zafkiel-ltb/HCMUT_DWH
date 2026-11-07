/* C3-02 | DATA CHANGE. BACK UP CompanyX_DW BEFORE EXECUTING.
   Does not re-run ETL, touch Fact/Dim tables or generate churn labels.
   Replaces CustomerSnapshot rows atomically. Run only after C3-00, C3-01.
*/
USE [CompanyX_DW];
GO
SET NOCOUNT ON;
SELECT COUNT_BIG(*) AS SnapshotRowsBefore,
       COUNT(DISTINCT SnapshotDate) AS SnapshotDatesBefore
FROM analytics.CustomerSnapshot;
GO
EXEC etl.usp_RebuildSnapshots;
GO
SELECT SnapshotDate,COUNT(*) AS CustomersWithPurchaseHistory,
       SUM(CASE WHEN Tenure IS NULL OR Share_Bikes IS NULL
                      OR Share_Accessories IS NULL OR Share_Clothing IS NULL
                      OR NSub IS NULL THEN 1 ELSE 0 END) AS IncompleteFeatureRows
FROM analytics.CustomerSnapshot
GROUP BY SnapshotDate ORDER BY SnapshotDate;
GO
