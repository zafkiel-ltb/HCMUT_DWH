/* C3-01 | INSTALL ONLY: replaces old four-date etl.usp_RebuildSnapshots.
   This installs a procedure but DOES NOT execute it or change existing Snapshot rows.
   Requires completed C1 schema + C2 facts; use C3-02 to rebuild.
*/
USE [CompanyX_DW];
GO
IF DB_NAME() <> N'CompanyX_DW'
    THROW 56301, N'Wrong database; select CompanyX_DW.', 1;
IF OBJECT_ID(N'analytics.CustomerSnapshot',N'U') IS NULL
    THROW 56302, N'Missing analytics.CustomerSnapshot (C1/C2 required).', 1;
IF COL_LENGTH(N'analytics.CustomerSnapshot',N'Tenure') IS NULL
 OR COL_LENGTH(N'analytics.CustomerSnapshot',N'Share_Bikes') IS NULL
 OR COL_LENGTH(N'analytics.CustomerSnapshot',N'Share_Accessories') IS NULL
 OR COL_LENGTH(N'analytics.CustomerSnapshot',N'Share_Clothing') IS NULL
 OR COL_LENGTH(N'analytics.CustomerSnapshot',N'NSub') IS NULL
    THROW 56303, N'Missing C1 feature columns. Run C1 first.', 1;
GO
CREATE OR ALTER PROCEDURE etl.usp_RebuildSnapshots
AS
BEGIN
  SET NOCOUNT ON;
  SET XACT_ABORT ON;

  IF DB_NAME() <> N'CompanyX_DW'
      THROW 56304, N'Wrong target database.', 1;
  IF COL_LENGTH(N'analytics.CustomerSnapshot',N'Tenure') IS NULL
   OR COL_LENGTH(N'analytics.CustomerSnapshot',N'Share_Bikes') IS NULL
   OR COL_LENGTH(N'analytics.CustomerSnapshot',N'Share_Accessories') IS NULL
   OR COL_LENGTH(N'analytics.CustomerSnapshot',N'Share_Clothing') IS NULL
   OR COL_LENGTH(N'analytics.CustomerSnapshot',N'NSub') IS NULL
      THROW 56305, N'Feature columns missing; stop before changing data.', 1;
  IF NOT EXISTS(SELECT 1 FROM dbo.FactSalesOrder)
      THROW 56306, N'FactSalesOrder is empty.', 1;
  /* Do not silently invalidate already-produced model scores. */
  IF EXISTS (SELECT 1 FROM analytics.CustomerRiskScore)
      THROW 56307, N'CustomerRiskScore already contains rows. Review dependencies before rebuild.', 1;

  /* Dates: Jun-2013 through Feb-2014 (1st and 15th), Mar-01-2014,
     plus scoring date Jul-08-2014. 19 training/evaluation + 1 DSS = 20. */
  CREATE TABLE #Dates (SnapshotDate DATE NOT NULL PRIMARY KEY);
  DECLARE @m DATE=CONVERT(DATE,'20130601',112);
  WHILE @m <= CONVERT(DATE,'20140301',112)
  BEGIN
    INSERT #Dates(SnapshotDate) VALUES (@m);
    IF @m < CONVERT(DATE,'20140301',112)
      INSERT #Dates(SnapshotDate) VALUES (DATEADD(DAY,14,@m));
    SET @m=DATEADD(MONTH,1,@m);
  END;
  INSERT #Dates(SnapshotDate) VALUES (CONVERT(DATE,'20140708',112));
  IF (SELECT COUNT(*) FROM #Dates)<>20
      THROW 56308, N'Incorrect snapshot date grid.', 1;

  /* Eligible order: both order and shipment dates STRICTLY before T.
     FactSalesOrder has passed C2 in-scope / Status=5 filters.
     Monetary and Frequency are computed ONCE PER ORDER, never from lines. */
  SELECT d.SnapshotDate,dc.CustomerID,f.CustomerKey,f.SalesOrderID,
         dd.FullDate AS OrderDay,f.TotalDue
  INTO #EligibleOrders
  FROM #Dates d
  JOIN dbo.FactSalesOrder f ON f.[Status]=5 AND f.ShipDate < d.SnapshotDate
  JOIN dbo.DimDate dd ON dd.DateKey=f.OrderDateKey AND dd.FullDate < d.SnapshotDate
  JOIN dbo.DimCustomer dc ON dc.CustomerKey=f.CustomerKey;
  IF NOT EXISTS(SELECT 1 FROM #EligibleOrders)
      THROW 56309, N'No eligible orders at any snapshot date.', 1;
  CREATE CLUSTERED INDEX IX_C3_Eligible ON #EligibleOrders
       (SnapshotDate,CustomerID,SalesOrderID);

  SELECT e.CustomerID,e.SnapshotDate,MAX(e.CustomerKey) AS CustomerKey,
         DATEDIFF(DAY,MAX(e.OrderDay),e.SnapshotDate) AS RecencyDays,
         COUNT(*) AS Frequency,
         CAST(SUM(e.TotalDue) AS DECIMAL(19,4)) AS Monetary,
         SUM(CASE WHEN e.OrderDay>=DATEADD(DAY,-90,e.SnapshotDate)
                      THEN 1 ELSE 0 END) AS OrdersLast90Days,
         SUM(CASE WHEN e.OrderDay>=DATEADD(DAY,-180,e.SnapshotDate)
                      THEN 1 ELSE 0 END) AS OrdersLast180Days,
         DATEDIFF(DAY,MIN(e.OrderDay),e.SnapshotDate) AS Tenure
  INTO #HeadAgg
  FROM #EligibleOrders e
  GROUP BY e.CustomerID,e.SnapshotDate;
  CREATE UNIQUE CLUSTERED INDEX IX_C3_Head ON #HeadAgg(CustomerID,SnapshotDate);

  /* Product CATEGORY ratios use the sum of ALL purchased line totals as
     denominator (including Components and unclassified products).
     Thus three displayed shares need not sum to one.
     NSub counts distinct, non-NULL purchased subcategory IDs. */
  SELECT e.CustomerID,e.SnapshotDate,
         SUM(l.LineTotal) AS AllLineTotal,
         SUM(CASE WHEN p.CategoryName=N'Bikes' THEN l.LineTotal ELSE 0 END) AS BikeLineTotal,
         SUM(CASE WHEN p.CategoryName=N'Accessories' THEN l.LineTotal ELSE 0 END) AS AccessoryLineTotal,
         SUM(CASE WHEN p.CategoryName=N'Clothing' THEN l.LineTotal ELSE 0 END) AS ClothingLineTotal,
         COUNT(DISTINCT p.SubcategoryID) AS NSub
  INTO #LineAgg
  FROM #EligibleOrders e
  JOIN dbo.FactSalesOrderLine l ON l.SalesOrderID=e.SalesOrderID
  JOIN dbo.DimProduct p ON p.ProductKey=l.ProductKey
  GROUP BY e.CustomerID,e.SnapshotDate;
  CREATE UNIQUE CLUSTERED INDEX IX_C3_Line ON #LineAgg(CustomerID,SnapshotDate);

  /* Fail before touching existing snapshots if line details are absent or
     denominator nonpositive. Do not silently turn undefined shares into zero. */
  IF EXISTS (
      SELECT 1 FROM #HeadAgg h LEFT JOIN #LineAgg a
       ON a.CustomerID=h.CustomerID AND a.SnapshotDate=h.SnapshotDate
      WHERE a.CustomerID IS NULL OR a.AllLineTotal<=0
  ) THROW 56310, N'At least one eligible customer/date lacks positive line totals.', 1;

  SELECT h.CustomerID,h.SnapshotDate,h.CustomerKey,h.RecencyDays,h.Frequency,
         h.Monetary,h.OrdersLast90Days,h.OrdersLast180Days,h.Tenure,
         CAST(a.BikeLineTotal/NULLIF(a.AllLineTotal,0) AS DECIMAL(9,6)) AS Share_Bikes,
         CAST(a.AccessoryLineTotal/NULLIF(a.AllLineTotal,0) AS DECIMAL(9,6)) AS Share_Accessories,
         CAST(a.ClothingLineTotal/NULLIF(a.AllLineTotal,0) AS DECIMAL(9,6)) AS Share_Clothing,
         a.NSub
  INTO #NewSnapshot
  FROM #HeadAgg h JOIN #LineAgg a
    ON a.CustomerID=h.CustomerID AND a.SnapshotDate=h.SnapshotDate;

  IF (SELECT COUNT(DISTINCT SnapshotDate) FROM #NewSnapshot)<>20
      THROW 56311, N'Missing one or more planned snapshot dates.', 1;
  IF EXISTS (SELECT 1 FROM #NewSnapshot WHERE RecencyDays<1 OR Tenure<RecencyDays
                  OR Frequency<1 OR OrdersLast90Days>OrdersLast180Days
                  OR OrdersLast180Days>Frequency OR NSub<0
                  OR Monetary<0 OR Share_Bikes NOT BETWEEN 0 AND 1
                  OR Share_Accessories NOT BETWEEN 0 AND 1
                  OR Share_Clothing NOT BETWEEN 0 AND 1
                  OR Share_Bikes+Share_Accessories+Share_Clothing>1.000003)
      THROW 56312, N'New features failed domain checks; old snapshots preserved.', 1;

  /* Atomic replacement is necessary because CURRENT existing table PK is only
     (CustomerID,SnapshotDate) and it still contains four obsolete snapshot dates.
     Any SQL error rolls back DELETE and INSERT in one transaction. */
  BEGIN TRY
    BEGIN TRANSACTION;
    DELETE FROM analytics.CustomerSnapshot;
    INSERT analytics.CustomerSnapshot
       (CustomerID,SnapshotDate,CustomerKey,RecencyDays,Frequency,Monetary,
        OrdersLast90Days,OrdersLast180Days,Tenure,
        Share_Bikes,Share_Accessories,Share_Clothing,NSub)
    SELECT CustomerID,SnapshotDate,CustomerKey,RecencyDays,Frequency,Monetary,
           OrdersLast90Days,OrdersLast180Days,Tenure,
           Share_Bikes,Share_Accessories,Share_Clothing,NSub
    FROM #NewSnapshot;
    DECLARE @InsertedRows INT=@@ROWCOUNT;
    IF @InsertedRows<>(SELECT COUNT(*) FROM #NewSnapshot)
        THROW 56313, N'Snapshot insert row count mismatch.', 1;
    COMMIT TRANSACTION;
  END TRY
  BEGIN CATCH
    IF @@TRANCOUNT>0 ROLLBACK TRANSACTION;
    THROW;
  END CATCH;

  SELECT COUNT_BIG(*) AS SnapshotRows,
         COUNT(DISTINCT SnapshotDate) AS SnapshotDates,
         MIN(SnapshotDate) AS FirstDate,
         MAX(SnapshotDate) AS LastDate,
         SUM(CASE WHEN Tenure IS NULL OR Share_Bikes IS NULL
                        OR Share_Accessories IS NULL OR Share_Clothing IS NULL
                        OR NSub IS NULL THEN 1 ELSE 0 END) AS IncompleteFeatureRows
  FROM analytics.CustomerSnapshot;
  PRINT N'C3_SNAPSHOT_REBUILD_SUCCESS: 19 historical dates + 1 DSS date; 5 added features populated.';
END;
GO
PRINT N'C3_INSTALL_OK: procedure replaced. NO snapshot rows have been changed yet.';
GO
