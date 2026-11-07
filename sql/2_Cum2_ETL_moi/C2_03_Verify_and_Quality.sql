/* ===========================================================================
   CLUSTER 2: READ-ONLY QUALITY VERIFICATION AFTER RUNNING C2_02_Run_ETL_ONLY.py
   Does not re-run ETL, rebuild Snapshot, or alter permanent data.
   PASS means THIS check passed, not that all data problems are absent.
   Counts are calculated from the latest ETL run, excluding ONLY in-scope
   rejected records from the eligible-fact reconciliation.
   =========================================================================== */
USE [CompanyX_DW];
GO
SET NOCOUNT ON;
DECLARE @RunID UNIQUEIDENTIFIER = (
   SELECT TOP (1) RunID FROM etl.RunLog ORDER BY StartedAt DESC,FinishedAt DESC);
IF @RunID IS NULL THROW 55301, N'No ETL run in etl.RunLog.', 1;
IF COL_LENGTH(N'etl.RejectedRow',N'IsInScope') IS NULL
   THROW 55302, N'Missing IsInScope: run Cluster 1 upgrade first.', 1;
SELECT @RunID AS CheckedRunID;
DROP TABLE IF EXISTS #QA;
CREATE TABLE #QA (
  GroupName NVARCHAR(60) NOT NULL,
  CheckName NVARCHAR(160) NOT NULL,
  FailedCount BIGINT NOT NULL,
  Details NVARCHAR(200) NULL
);

/* Source-derived expected FACT IDs: exclude ONLY in-scope rejections. */
DROP TABLE IF EXISTS #ExpectedOrders;
SELECT o.SalesOrderID INTO #ExpectedOrders
FROM CompanyX.Sales.SalesOrderHeader o
JOIN CompanyX.Sales.Customer c ON c.CustomerID=o.CustomerID
WHERE o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
 AND NOT EXISTS (
   SELECT 1 FROM etl.RejectedRow r
   WHERE r.RunID=@RunID AND r.EntityType=N'Order' AND r.IsInScope=1
    AND r.SourceKey=CONVERT(NVARCHAR(100),o.SalesOrderID));
CREATE UNIQUE CLUSTERED INDEX CX_ExpectedOrders ON #ExpectedOrders(SalesOrderID);
DROP TABLE IF EXISTS #ExpectedLines;
SELECT l.SalesOrderID,l.SalesOrderDetailID INTO #ExpectedLines
FROM CompanyX.Sales.SalesOrderDetail l
JOIN #ExpectedOrders o ON o.SalesOrderID=l.SalesOrderID
WHERE NOT EXISTS (
    SELECT 1 FROM etl.RejectedRow r
    WHERE r.RunID=@RunID AND r.EntityType=N'OrderLine' AND r.IsInScope=1
    AND r.SourceKey=CONCAT(CONVERT(NVARCHAR(20),l.SalesOrderID),N':',CONVERT(NVARCHAR(20),l.SalesOrderDetailID)));
CREATE UNIQUE CLUSTERED INDEX CX_ExpectedLines ON #ExpectedLines(SalesOrderID,SalesOrderDetailID);

/* 1. Counts */
INSERT #QA SELECT N'01. Số dòng',N'DimCustomer -- khách cá nhân',
 ABS((SELECT COUNT_BIG(*) FROM dbo.DimCustomer)-
     (SELECT COUNT_BIG(*) FROM CompanyX.Sales.Customer WHERE PersonID IS NOT NULL AND StoreID IS NULL)),NULL;
INSERT #QA SELECT N'01. Số dòng',N'DimProduct',
 ABS((SELECT COUNT_BIG(*) FROM dbo.DimProduct)-
     (SELECT COUNT_BIG(*) FROM CompanyX.Production.Product)),NULL;
INSERT #QA SELECT N'01. Số dòng',N'DimTerritory',
 ABS((SELECT COUNT_BIG(*) FROM dbo.DimTerritory)-
     (SELECT COUNT_BIG(*) FROM CompanyX.Sales.SalesTerritory)),NULL;
INSERT #QA SELECT N'01. Số dòng',N'DimDate lịch liên tục',
 ABS((SELECT COUNT_BIG(*) FROM dbo.DimDate)-
     (SELECT DATEDIFF(DAY,MIN(CONVERT(DATE,OrderDate)),MAX(CONVERT(DATE,OrderDate)))+1
       FROM CompanyX.Sales.SalesOrderHeader)),NULL;
INSERT #QA SELECT N'01. Số dòng',N'FactSalesOrder -- in-scope & valid',
 ABS((SELECT COUNT_BIG(*) FROM dbo.FactSalesOrder)-(SELECT COUNT_BIG(*) FROM #ExpectedOrders)),NULL;
INSERT #QA SELECT N'01. Số dòng',N'FactSalesOrderLine -- in-scope & valid',
 ABS((SELECT COUNT_BIG(*) FROM dbo.FactSalesOrderLine)-(SELECT COUNT_BIG(*) FROM #ExpectedLines)),NULL;
INSERT #QA SELECT N'01. Số dòng',N'Staging OrderRaw đủ toàn nguồn',
 ABS((SELECT COUNT_BIG(*) FROM stg.OrderRaw)-
     (SELECT COUNT_BIG(*) FROM CompanyX.Sales.SalesOrderHeader)),NULL;
INSERT #QA SELECT N'01. Số dòng',N'Staging OrderLineRaw đủ toàn nguồn',
 ABS((SELECT COUNT_BIG(*) FROM stg.OrderLineRaw)-
     (SELECT COUNT_BIG(*) FROM CompanyX.Sales.SalesOrderDetail)),NULL;

/* 2. Keys: symmetric exact identifier comparison */
INSERT #QA SELECT N'02. Mã nguồn',N'CustomerID thiếu',COUNT_BIG(*),NULL FROM (
  SELECT CustomerID FROM CompanyX.Sales.Customer WHERE PersonID IS NOT NULL AND StoreID IS NULL
  EXCEPT SELECT CustomerID FROM dbo.DimCustomer) x;
INSERT #QA SELECT N'02. Mã nguồn',N'CustomerID thừa',COUNT_BIG(*),NULL FROM (
  SELECT CustomerID FROM dbo.DimCustomer
  EXCEPT SELECT CustomerID FROM CompanyX.Sales.Customer WHERE PersonID IS NOT NULL AND StoreID IS NULL) x;
INSERT #QA SELECT N'02. Mã nguồn',N'SalesOrderID thiếu',COUNT_BIG(*),NULL FROM (
  SELECT SalesOrderID FROM #ExpectedOrders
  EXCEPT SELECT SalesOrderID FROM dbo.FactSalesOrder) x;
INSERT #QA SELECT N'02. Mã nguồn',N'SalesOrderID thừa',COUNT_BIG(*),NULL FROM (
  SELECT SalesOrderID FROM dbo.FactSalesOrder
  EXCEPT SELECT SalesOrderID FROM #ExpectedOrders) x;
INSERT #QA SELECT N'02. Mã nguồn',N'OrderLine composite key thiếu',COUNT_BIG(*),NULL FROM (
  SELECT SalesOrderID,SalesOrderDetailID FROM #ExpectedLines
  EXCEPT SELECT SalesOrderID,SalesOrderDetailID FROM dbo.FactSalesOrderLine) x;
INSERT #QA SELECT N'02. Mã nguồn',N'OrderLine composite key thừa',COUNT_BIG(*),NULL FROM (
  SELECT SalesOrderID,SalesOrderDetailID FROM dbo.FactSalesOrderLine
  EXCEPT SELECT SalesOrderID,SalesOrderDetailID FROM #ExpectedLines) x;
INSERT #QA SELECT N'02. Mã nguồn',N'ProductID thiếu/thừa',
 (SELECT COUNT_BIG(*) FROM (SELECT ProductID FROM CompanyX.Production.Product
   EXCEPT SELECT ProductID FROM dbo.DimProduct) x)
 +(SELECT COUNT_BIG(*) FROM (SELECT ProductID FROM dbo.DimProduct
   EXCEPT SELECT ProductID FROM CompanyX.Production.Product) y),NULL;
INSERT #QA SELECT N'02. Mã nguồn',N'TerritoryID thiếu/thừa',
 (SELECT COUNT_BIG(*) FROM (SELECT TerritoryID FROM CompanyX.Sales.SalesTerritory
   EXCEPT SELECT TerritoryID FROM dbo.DimTerritory) x)
 +(SELECT COUNT_BIG(*) FROM (SELECT TerritoryID FROM dbo.DimTerritory
   EXCEPT SELECT TerritoryID FROM CompanyX.Sales.SalesTerritory) y),NULL;

/* 3. Uniqueness and relations */
INSERT #QA SELECT N'03. Khóa',N'DimCustomer.CustomerID trùng',COUNT_BIG(*),NULL FROM (
   SELECT CustomerID FROM dbo.DimCustomer GROUP BY CustomerID HAVING COUNT(*)>1) x;
INSERT #QA SELECT N'03. Khóa',N'FactSalesOrder.SalesOrderID trùng',COUNT_BIG(*),NULL FROM (
   SELECT SalesOrderID FROM dbo.FactSalesOrder GROUP BY SalesOrderID HAVING COUNT(*)>1) x;
INSERT #QA SELECT N'03. Khóa',N'FactSalesOrderLine composite key trùng',COUNT_BIG(*),NULL FROM (
   SELECT SalesOrderID,SalesOrderDetailID FROM dbo.FactSalesOrderLine
   GROUP BY SalesOrderID,SalesOrderDetailID HAVING COUNT(*)>1) x;
INSERT #QA SELECT N'03. Khóa',N'FactSalesOrder thiếu dimension',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrder f
LEFT JOIN dbo.DimCustomer c ON c.CustomerKey=f.CustomerKey
LEFT JOIN dbo.DimDate d ON d.DateKey=f.OrderDateKey
LEFT JOIN dbo.DimTerritory t ON t.TerritoryKey=f.TerritoryKey
WHERE c.CustomerKey IS NULL OR d.DateKey IS NULL
 OR (f.TerritoryKey IS NOT NULL AND t.TerritoryKey IS NULL);
INSERT #QA SELECT N'03. Khóa',N'FactSalesOrderLine thiếu dimension',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrderLine l
LEFT JOIN dbo.DimCustomer c ON c.CustomerKey=l.CustomerKey
LEFT JOIN dbo.DimDate d ON d.DateKey=l.OrderDateKey
LEFT JOIN dbo.DimProduct p ON p.ProductKey=l.ProductKey
LEFT JOIN dbo.DimTerritory t ON t.TerritoryKey=l.TerritoryKey
WHERE c.CustomerKey IS NULL OR d.DateKey IS NULL OR p.ProductKey IS NULL
 OR (l.TerritoryKey IS NOT NULL AND t.TerritoryKey IS NULL);
INSERT #QA SELECT N'03. Khóa',N'FactLine lệch khóa cha',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrderLine l
LEFT JOIN dbo.FactSalesOrder f ON f.SalesOrderID=l.SalesOrderID
WHERE f.SalesOrderID IS NULL OR l.CustomerKey<>f.CustomerKey
 OR l.OrderDateKey<>f.OrderDateKey
 OR l.TerritoryKey<>f.TerritoryKey
 OR (l.TerritoryKey IS NULL AND f.TerritoryKey IS NOT NULL)
 OR (l.TerritoryKey IS NOT NULL AND f.TerritoryKey IS NULL);

/* 4. Scope and mapping */
INSERT #QA SELECT N'04. Phạm vi/ánh xạ',N'DimCustomer ngoài scope cá nhân',COUNT_BIG(*),NULL
FROM dbo.DimCustomer d LEFT JOIN CompanyX.Sales.Customer c ON c.CustomerID=d.CustomerID
WHERE c.CustomerID IS NULL OR c.PersonID IS NULL OR c.StoreID IS NOT NULL
   OR d.PersonID<>c.PersonID;
INSERT #QA SELECT N'04. Phạm vi/ánh xạ',N'FactOrder sai status/ship/date/money',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrder f JOIN dbo.DimDate d ON d.DateKey=f.OrderDateKey
WHERE f.Status<>5 OR f.ShipDate IS NULL OR f.ShipDate<d.FullDate OR f.DueDate<d.FullDate
 OR f.SubTotal<=0 OR f.TaxAmt<0 OR f.Freight<0 OR f.TotalDue<0;
INSERT #QA SELECT N'04. Phạm vi/ánh xạ',N'FactLine sai qty/price/discount',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrderLine l
JOIN dbo.DimProduct p ON p.ProductKey=l.ProductKey
JOIN CompanyX.Production.Product sp ON sp.ProductID=p.ProductID
JOIN CompanyX.Sales.SalesOrderDetail ol
  ON ol.SalesOrderID=l.SalesOrderID AND ol.SalesOrderDetailID=l.SalesOrderDetailID
WHERE l.OrderQty<=0 OR l.UnitPrice<0 OR l.UnitPriceDiscount NOT BETWEEN 0 AND 1
 OR (l.UnitPrice=0 AND sp.ListPrice>0 AND ol.SpecialOfferID=1)
 OR ABS(l.LineTotal-l.OrderQty*l.UnitPrice*(1-l.UnitPriceDiscount))>0.01;
INSERT #QA SELECT N'04. Phạm vi/ánh xạ',N'FactOrder sai Customer/Date/Territory',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrder f
JOIN dbo.DimCustomer d ON d.CustomerKey=f.CustomerKey
JOIN dbo.DimDate dt ON dt.DateKey=f.OrderDateKey
LEFT JOIN dbo.DimTerritory t ON t.TerritoryKey=f.TerritoryKey
LEFT JOIN CompanyX.Sales.SalesOrderHeader so ON so.SalesOrderID=f.SalesOrderID
WHERE so.SalesOrderID IS NULL OR so.CustomerID<>d.CustomerID
 OR CONVERT(DATE,so.OrderDate)<>dt.FullDate
 OR t.TerritoryID<>so.TerritoryID
 OR (t.TerritoryID IS NULL AND so.TerritoryID IS NOT NULL)
 OR (t.TerritoryID IS NOT NULL AND so.TerritoryID IS NULL);
INSERT #QA SELECT N'04. Phạm vi/ánh xạ',N'FactLine sai ProductID nguồn',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrderLine l
JOIN dbo.DimProduct p ON p.ProductKey=l.ProductKey
LEFT JOIN CompanyX.Sales.SalesOrderDetail so
  ON so.SalesOrderID=l.SalesOrderID AND so.SalesOrderDetailID=l.SalesOrderDetailID
WHERE so.SalesOrderID IS NULL OR so.ProductID<>p.ProductID;
INSERT #QA SELECT N'04. Phạm vi/ánh xạ',N'FactOrder sai giá trị nguồn',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrder f
LEFT JOIN CompanyX.Sales.SalesOrderHeader o ON o.SalesOrderID=f.SalesOrderID
WHERE o.SalesOrderID IS NULL OR ABS(f.SubTotal-o.SubTotal)>0.0001
 OR ABS(f.TaxAmt-o.TaxAmt)>0.0001 OR ABS(f.Freight-o.Freight)>0.0001
 OR ABS(f.TotalDue-o.TotalDue)>0.0001;
INSERT #QA SELECT N'04. Phạm vi/ánh xạ',N'FactLine sai giá trị nguồn',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrderLine l
LEFT JOIN CompanyX.Sales.SalesOrderDetail o
  ON o.SalesOrderID=l.SalesOrderID AND o.SalesOrderDetailID=l.SalesOrderDetailID
WHERE o.SalesOrderID IS NULL OR l.OrderQty<>o.OrderQty
 OR ABS(l.UnitPrice-o.UnitPrice)>0.0001
 OR ABS(l.UnitPriceDiscount-o.UnitPriceDiscount)>0.0001
 OR ABS(l.LineTotal-o.LineTotal)>0.0001;
INSERT #QA SELECT N'04. Phạm vi/ánh xạ',N'DimDate attributes sai',COUNT_BIG(*),NULL
FROM dbo.DimDate d
WHERE d.DateKey<>CONVERT(INT,CONVERT(CHAR(8),d.FullDate,112))
 OR d.[Day]<>DAY(d.FullDate) OR d.[Month]<>MONTH(d.FullDate)
 OR d.[Quarter]<>DATEPART(QUARTER,d.FullDate) OR d.[Year]<>YEAR(d.FullDate);

/* 5. Financial comparisons (with the SAME eligible population after rejection) */
DECLARE @SourceSub DECIMAL(38,4)=(
 SELECT SUM(CAST(o.SubTotal AS DECIMAL(38,4)))
 FROM CompanyX.Sales.SalesOrderHeader o JOIN #ExpectedOrders e ON e.SalesOrderID=o.SalesOrderID);
DECLARE @DWSub DECIMAL(38,4)=(SELECT SUM(CAST(SubTotal AS DECIMAL(38,4))) FROM dbo.FactSalesOrder);
DECLARE @SourceDue DECIMAL(38,4)=(
 SELECT SUM(CAST(o.TotalDue AS DECIMAL(38,4)))
 FROM CompanyX.Sales.SalesOrderHeader o JOIN #ExpectedOrders e ON e.SalesOrderID=o.SalesOrderID);
DECLARE @DWDue DECIMAL(38,4)=(SELECT SUM(CAST(TotalDue AS DECIMAL(38,4))) FROM dbo.FactSalesOrder);
INSERT #QA SELECT N'05. Tiền',N'Tổng SubTotal nguồn hợp lệ vs DW',
 IIF(ABS(ISNULL(@SourceSub,0)-ISNULL(@DWSub,0))<=0.01,0,1),
 CONCAT(CONVERT(VARCHAR(40),@SourceSub),N' vs ',CONVERT(VARCHAR(40),@DWSub));
INSERT #QA SELECT N'05. Tiền',N'Tổng TotalDue nguồn hợp lệ vs DW',
 IIF(ABS(ISNULL(@SourceDue,0)-ISNULL(@DWDue,0))<=0.01,0,1),
 CONCAT(CONVERT(VARCHAR(40),@SourceDue),N' vs ',CONVERT(VARCHAR(40),@DWDue));
INSERT #QA SELECT N'05. Tiền',N'TotalDue = SubTotal+TaxAmt+Freight',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrder
WHERE ABS(TotalDue-(SubTotal+TaxAmt+Freight))>0.01;
INSERT #QA SELECT N'05. Tiền',N'FactLine sum vs FactOrder SubTotal',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrder f
LEFT JOIN (SELECT SalesOrderID,SUM(CAST(LineTotal AS DECIMAL(38,4))) AS SumLines
   FROM dbo.FactSalesOrderLine GROUP BY SalesOrderID) l ON l.SalesOrderID=f.SalesOrderID
WHERE l.SalesOrderID IS NULL OR ABS(f.SubTotal-l.SumLines)>0.01;

/* 6. All-stage rejection coverage, flags, duplicates and load-exclusion */
INSERT #QA SELECT N'06. Rejection',N'Đơn SubTotal<=0 có dòng chưa log lỗi',COUNT_BIG(*),NULL
FROM stg.OrderRaw o
WHERE o.SubTotal<=0 AND EXISTS (
  SELECT 1 FROM stg.OrderLineRaw l WHERE l.SalesOrderID=o.SalesOrderID)
 AND NOT EXISTS (SELECT 1 FROM etl.RejectedRow r WHERE r.RunID=@RunID
  AND r.EntityType=N'Order' AND r.SourceKey=CONVERT(NVARCHAR(100),o.SalesOrderID));
INSERT #QA SELECT N'06. Rejection',N'Dòng UnitPrice=0, ListPrice>0, no offer chưa log',COUNT_BIG(*),NULL
FROM stg.OrderLineRaw l
JOIN stg.ProductRaw p ON p.ProductID=l.ProductID
WHERE l.UnitPrice=0 AND p.ListPrice>0 AND ISNULL(l.SpecialOfferID,1)=1
 AND NOT EXISTS (SELECT 1 FROM etl.RejectedRow r WHERE r.RunID=@RunID
   AND r.EntityType=N'OrderLine' AND r.SourceKey=CONCAT(CONVERT(NVARCHAR(20),l.SalesOrderID),N':',CONVERT(NVARCHAR(20),l.SalesOrderDetailID)));
INSERT #QA SELECT N'06. Rejection',N'RejectedRow.IsInScope sai (Order)',COUNT_BIG(*),NULL
FROM etl.RejectedRow r
LEFT JOIN stg.OrderRaw o ON r.EntityType=N'Order' AND r.SourceKey=CONVERT(NVARCHAR(100),o.SalesOrderID)
LEFT JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
WHERE r.RunID=@RunID AND r.EntityType=N'Order'
 AND (r.IsInScope IS NULL OR o.SalesOrderID IS NULL OR
  r.IsInScope<>CAST(CASE WHEN o.Status=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
      THEN 1 ELSE 0 END AS BIT));
INSERT #QA SELECT N'06. Rejection',N'RejectedRow.IsInScope sai (OrderLine)',COUNT_BIG(*),NULL
FROM etl.RejectedRow r
LEFT JOIN stg.OrderLineRaw l ON r.EntityType=N'OrderLine'
 AND r.SourceKey=CONCAT(CONVERT(NVARCHAR(20),l.SalesOrderID),N':',CONVERT(NVARCHAR(20),l.SalesOrderDetailID))
LEFT JOIN stg.OrderRaw o ON o.SalesOrderID=l.SalesOrderID
LEFT JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
WHERE r.RunID=@RunID AND r.EntityType=N'OrderLine'
 AND (r.IsInScope IS NULL OR l.SalesOrderID IS NULL OR
  r.IsInScope<>CAST(CASE WHEN o.Status=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
      THEN 1 ELSE 0 END AS BIT));
INSERT #QA SELECT N'06. Rejection',N'RejectedRow trùng entity+source trong 1 lần chạy',COUNT_BIG(*),NULL
FROM (SELECT EntityType,SourceKey FROM etl.RejectedRow WHERE RunID=@RunID
      GROUP BY EntityType,SourceKey HAVING COUNT(*)>1) x;
INSERT #QA SELECT N'06. Rejection',N'Fact chứa đơn đã bị Reject in-scope',COUNT_BIG(*),NULL
FROM dbo.FactSalesOrder f
JOIN etl.RejectedRow r ON r.RunID=@RunID AND r.EntityType=N'Order'
 AND r.IsInScope=1 AND r.SourceKey=CONVERT(NVARCHAR(100),f.SalesOrderID);

/* 7. Run/StepLog audit */
INSERT #QA SELECT N'07. Nhật ký',N'Last run SUCCESS',
  IIF(EXISTS(SELECT 1 FROM etl.RunLog WHERE RunID=@RunID AND Status=N'SUCCESS'
          AND ErrorMessage IS NULL),0,1),NULL;
INSERT #QA SELECT N'07. Nhật ký',N'Source=Loaded+Excluded+Rejected Fact steps',COUNT_BIG(*),NULL
FROM etl.StepLog
WHERE RunID=@RunID AND StepName IN (N'Load.FactSalesOrder',N'Load.FactSalesOrderLine')
 AND SourceRows<>LoadedRows+ExcludedRows+RejectedRows;
INSERT #QA SELECT N'07. Nhật ký',N'StepLog RejectedRows chỉ đếm in-scope',COUNT_BIG(*),NULL
FROM etl.StepLog s
WHERE s.RunID=@RunID AND (
  (s.StepName=N'Load.FactSalesOrder' AND s.RejectedRows<>(SELECT COUNT(*) FROM etl.RejectedRow r
     WHERE r.RunID=@RunID AND r.EntityType=N'Order' AND r.IsInScope=1))
  OR (s.StepName=N'Load.FactSalesOrderLine' AND s.RejectedRows<>(SELECT COUNT(*) FROM etl.RejectedRow r
     WHERE r.RunID=@RunID AND r.EntityType=N'OrderLine' AND r.IsInScope=1)));
INSERT #QA SELECT N'07. Nhật ký',N'Đủ hai bước Load.Fact trong StepLog',
 IIF((SELECT COUNT(*) FROM etl.StepLog WHERE RunID=@RunID
     AND StepName IN(N'Load.FactSalesOrder',N'Load.FactSalesOrderLine'))=2,0,1),NULL;

/* Main PASS/FAIL result. Actual test count is generated, never hardcoded. */
SELECT GroupName,CheckName,FailedCount,
       CASE WHEN FailedCount=0 THEN N'PASS' ELSE N'FAIL' END AS Result,Details
FROM #QA ORDER BY GroupName,CheckName;
SELECT COUNT(*) AS TotalChecks,
       SUM(CASE WHEN FailedCount=0 THEN 1 ELSE 0 END) AS Passed,
       SUM(CASE WHEN FailedCount>0 THEN 1 ELSE 0 END) AS Failed
FROM #QA;
SELECT GroupName,COUNT(*) AS Tests,
       SUM(CASE WHEN FailedCount=0 THEN 1 ELSE 0 END) AS Passed,
       SUM(CASE WHEN FailedCount>0 THEN 1 ELSE 0 END) AS Failed
FROM #QA GROUP BY GroupName ORDER BY GroupName;

/* Snapshot rows are NOT changed by C2_02. Cluster 3 will rebuild them. */
SELECT SnapshotDate,COUNT(*) AS RowsStillPresent,
       SUM(CASE WHEN Tenure IS NULL THEN 1 ELSE 0 END) AS TenureNotComputed
FROM analytics.CustomerSnapshot GROUP BY SnapshotDate ORDER BY SnapshotDate;

/* Additional diagnostic results for screenshots: */ 
/* A. Last run step breakdown */
SELECT StepName,SourceRows,LoadedRows,ExcludedRows,RejectedRows,
  SourceRows-LoadedRows-ExcludedRows-RejectedRows AS AccountingDiff
FROM etl.StepLog
WHERE RunID=@RunID AND StepName IN (N'Load.FactSalesOrder',N'Load.FactSalesOrderLine');
/* B. Total defect LOG by scope (not same as StepLog rejected, which is scoped). */
SELECT EntityType,IsInScope,COUNT(*) AS DefectsLogged
FROM etl.RejectedRow WHERE RunID=@RunID
GROUP BY EntityType,IsInScope ORDER BY EntityType,IsInScope;
/* C. Check targeted IDs without assuming these six MUST be erroneous. */
SELECT o.SalesOrderID,o.[Status],o.SubTotal,
       CASE WHEN o.[Status]=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
            THEN 1 ELSE 0 END AS IsInScope,
       r.RejectReason,
       CASE WHEN f.SalesOrderID IS NULL THEN 0 ELSE 1 END AS LoadedInFact
FROM stg.OrderRaw o
LEFT JOIN stg.CustomerRaw c ON c.CustomerID=o.CustomerID
LEFT JOIN etl.RejectedRow r ON r.RunID=@RunID AND r.EntityType=N'Order'
 AND r.SourceKey=CONVERT(NVARCHAR(100),o.SalesOrderID)
LEFT JOIN dbo.FactSalesOrder f ON f.SalesOrderID=o.SalesOrderID
WHERE o.SalesOrderID BETWEEN 43677 AND 43682
ORDER BY o.SalesOrderID;
/* D. Status */
SELECT RunID,StartedAt,FinishedAt,Status,ErrorMessage
FROM etl.RunLog WHERE RunID=@RunID;
GO
