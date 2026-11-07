/* C3-00 | PRE-FLIGHT, READ-ONLY | CompanyX_DW, SQL Server 2025.
   Do not use this script to rebuild snapshots. Inspect all result sets.
*/
USE [CompanyX_DW];
GO
SET NOCOUNT ON;

SELECT DB_NAME() AS TargetDatabase,
       (SELECT COUNT_BIG(*) FROM dbo.DimCustomer) AS DimCustomerRows,
       (SELECT COUNT_BIG(*) FROM dbo.FactSalesOrder) AS FactOrderRows,
       (SELECT COUNT_BIG(*) FROM dbo.FactSalesOrderLine) AS FactLineRows,
       (SELECT COUNT_BIG(*) FROM analytics.CustomerSnapshot) AS SnapshotRowsBefore,
       (SELECT COUNT(DISTINCT SnapshotDate) FROM analytics.CustomerSnapshot) AS SnapshotDatesBefore;

SELECT c.name AS FeatureColumn,
       CASE WHEN COL_LENGTH(N'analytics.CustomerSnapshot',c.name) IS NULL
            THEN N'MISSING' ELSE N'READY' END AS ColumnStatus
FROM (VALUES (N'Tenure'), (N'Share_Bikes'), (N'Share_Accessories'),
             (N'Share_Clothing'),(N'NSub')) c(name);

SELECT CategoryID,CategoryName,COUNT(*) AS ProductCount
FROM dbo.DimProduct GROUP BY CategoryID,CategoryName ORDER BY CategoryID,CategoryName;

SELECT SUM(CASE WHEN f.ShipDate IS NULL THEN 1 ELSE 0 END) AS MissingShipDate,
       SUM(CASE WHEN f.[Status] <> 5 THEN 1 ELSE 0 END) AS NotShipped,
       SUM(CASE WHEN dd.DateKey IS NULL THEN 1 ELSE 0 END) AS MissingOrderDay,
       SUM(CASE WHEN l.SalesOrderID IS NULL THEN 1 ELSE 0 END) AS OrdersWithoutLines
FROM dbo.FactSalesOrder f
LEFT JOIN dbo.DimDate dd ON dd.DateKey=f.OrderDateKey
LEFT JOIN (SELECT DISTINCT SalesOrderID FROM dbo.FactSalesOrderLine) l
  ON l.SalesOrderID=f.SalesOrderID;

SELECT COUNT(*) AS OrdersWithLineTotalNonpositive
FROM dbo.FactSalesOrder f
JOIN (SELECT SalesOrderID,SUM(LineTotal) AS LineTotalSum
      FROM dbo.FactSalesOrderLine GROUP BY SalesOrderID) s
   ON s.SalesOrderID=f.SalesOrderID
WHERE s.LineTotalSum<=0;

SELECT COUNT(*) AS ExistingRiskScores
FROM analytics.CustomerRiskScore;

SELECT SnapshotDate,COUNT(*) AS Customers,
       SUM(CASE WHEN Tenure IS NULL OR Share_Bikes IS NULL OR NSub IS NULL THEN 1 ELSE 0 END)
         AS FeatureRowsNotYetComputed
FROM analytics.CustomerSnapshot
GROUP BY SnapshotDate ORDER BY SnapshotDate;
