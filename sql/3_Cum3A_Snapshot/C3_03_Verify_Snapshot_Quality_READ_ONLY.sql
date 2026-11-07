/* C3-03 | READ-ONLY SNAPSHOT DATA QUALITY (separate from 44 C2 ETL checks).
   Expected output: ALL PASS, Failed=0. Recomputes each metric from DW facts.
   Only temp tables are written; six Dim/Fact and real Snapshots are unchanged.
*/
USE [CompanyX_DW];
GO
SET NOCOUNT ON;
IF DB_NAME()<>N'CompanyX_DW' THROW 56401,N'Wrong database.',1;
IF OBJECT_ID(N'analytics.CustomerSnapshot',N'U') IS NULL
  THROW 56402,N'Missing CustomerSnapshot.',1;
IF COL_LENGTH(N'analytics.CustomerSnapshot',N'NSub') IS NULL
  THROW 56403,N'Missing feature columns. Run C1.',1;

CREATE TABLE #Dates (SnapshotDate DATE NOT NULL PRIMARY KEY);
DECLARE @d DATE=CONVERT(DATE,'20130601',112);
WHILE @d<=CONVERT(DATE,'20140301',112)
BEGIN
  INSERT #Dates VALUES (@d);
  IF @d<CONVERT(DATE,'20140301',112) INSERT #Dates VALUES(DATEADD(DAY,14,@d));
  SET @d=DATEADD(MONTH,1,@d);
END;
INSERT #Dates VALUES(CONVERT(DATE,'20140708',112));

/* Independently rebuild the expected source data for every snapshot date. */
SELECT s.SnapshotDate,dc.CustomerID,dc.CustomerKey,f.SalesOrderID,
       dd.FullDate AS OrderDay,f.TotalDue
INTO #QOrders
FROM #Dates s
JOIN dbo.FactSalesOrder f ON f.ShipDate<s.SnapshotDate AND f.[Status]=5
JOIN dbo.DimDate dd ON dd.DateKey=f.OrderDateKey AND dd.FullDate<s.SnapshotDate
JOIN dbo.DimCustomer dc ON dc.CustomerKey=f.CustomerKey;
CREATE CLUSTERED INDEX IX_C3_QOrders ON #QOrders(SnapshotDate,CustomerID,SalesOrderID);

SELECT CustomerID,SnapshotDate,MAX(CustomerKey) AS CustomerKey,
       COUNT(*) AS ExpectedFrequency, SUM(TotalDue) AS ExpectedMonetary,
       DATEDIFF(DAY,MAX(OrderDay),SnapshotDate) AS ExpectedRecency,
       DATEDIFF(DAY,MIN(OrderDay),SnapshotDate) AS ExpectedTenure,
       SUM(CASE WHEN OrderDay>=DATEADD(DAY,-90,SnapshotDate) THEN 1 ELSE 0 END) AS ExpectedOrders90,
       SUM(CASE WHEN OrderDay>=DATEADD(DAY,-180,SnapshotDate) THEN 1 ELSE 0 END) AS ExpectedOrders180
INTO #QHead
FROM #QOrders GROUP BY CustomerID,SnapshotDate;
CREATE UNIQUE CLUSTERED INDEX IX_C3_QHead ON #QHead(CustomerID,SnapshotDate);

SELECT q.CustomerID,q.SnapshotDate,
       SUM(l.LineTotal) AS TotalLines,
       SUM(CASE WHEN p.CategoryName=N'Bikes' THEN l.LineTotal ELSE 0 END) AS Bikes,
       SUM(CASE WHEN p.CategoryName=N'Accessories' THEN l.LineTotal ELSE 0 END) AS Accessories,
       SUM(CASE WHEN p.CategoryName=N'Clothing' THEN l.LineTotal ELSE 0 END) AS Clothing,
       COUNT(DISTINCT p.SubcategoryID) AS ExpectedNSub
INTO #QLines
FROM #QOrders q
JOIN dbo.FactSalesOrderLine l ON l.SalesOrderID=q.SalesOrderID
JOIN dbo.DimProduct p ON p.ProductKey=l.ProductKey
GROUP BY q.CustomerID,q.SnapshotDate;
CREATE UNIQUE CLUSTERED INDEX IX_C3_QLines ON #QLines(CustomerID,SnapshotDate);

CREATE TABLE #QA (
  Category NVARCHAR(80) NOT NULL,
  CheckName NVARCHAR(180) NOT NULL,
  FailedRows BIGINT NOT NULL
);
/* 01 Calendar / unique keys */
INSERT #QA SELECT N'01. Calendar',N'Exactly 20 distinct snapshot dates',
 CASE WHEN COUNT(DISTINCT SnapshotDate)=20 THEN 0 ELSE 1 END
FROM analytics.CustomerSnapshot;
INSERT #QA SELECT N'01. Calendar',N'No missing or unexpected dates',COUNT_BIG(*)
FROM (
    SELECT d.SnapshotDate FROM #Dates d
    WHERE NOT EXISTS (SELECT 1 FROM analytics.CustomerSnapshot s
                      WHERE s.SnapshotDate=d.SnapshotDate)
    UNION ALL
    SELECT DISTINCT s.SnapshotDate FROM analytics.CustomerSnapshot s
    WHERE NOT EXISTS (SELECT 1 FROM #Dates d
                      WHERE d.SnapshotDate=s.SnapshotDate)
) diff;
/* An explicit symmetric set difference avoids EXCEPT/UNION precedence pitfalls. */
INSERT #QA SELECT N'01. Calendar',N'All expected dates contain at least one customer',COUNT_BIG(*)
FROM #Dates d WHERE NOT EXISTS (
 SELECT 1 FROM analytics.CustomerSnapshot s WHERE s.SnapshotDate=d.SnapshotDate);
INSERT #QA SELECT N'01. Calendar',N'No duplicate (CustomerID,SnapshotDate)',COUNT_BIG(*)
FROM (SELECT CustomerID,SnapshotDate FROM analytics.CustomerSnapshot
      GROUP BY CustomerID,SnapshotDate HAVING COUNT(*)>1) bad;

/* 02 Coverage and dimensions */
INSERT #QA SELECT N'02. Coverage',N'No missing eligible customer/date rows',COUNT_BIG(*)
FROM #QHead h LEFT JOIN analytics.CustomerSnapshot s
 ON s.CustomerID=h.CustomerID AND s.SnapshotDate=h.SnapshotDate
WHERE s.CustomerID IS NULL;
INSERT #QA SELECT N'02. Coverage',N'No extra customer/date rows',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s LEFT JOIN #QHead h
 ON s.CustomerID=h.CustomerID AND s.SnapshotDate=h.SnapshotDate
WHERE h.CustomerID IS NULL;
INSERT #QA SELECT N'02. Coverage',N'CustomerKey agrees with customer dimension',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s LEFT JOIN dbo.DimCustomer d ON d.CustomerID=s.CustomerID
WHERE d.CustomerID IS NULL OR d.CustomerKey<>s.CustomerKey;
INSERT #QA SELECT N'02. Coverage',N'Exact customer count for each date',COUNT_BIG(*)
FROM #Dates d
LEFT JOIN (SELECT SnapshotDate,COUNT(*) AS n FROM #QHead GROUP BY SnapshotDate) e
 ON e.SnapshotDate=d.SnapshotDate
LEFT JOIN (SELECT SnapshotDate,COUNT(*) AS n FROM analytics.CustomerSnapshot GROUP BY SnapshotDate) a
 ON a.SnapshotDate=d.SnapshotDate
WHERE COALESCE(e.n,0)<>COALESCE(a.n,0);

/* 03 Feature non-null and plausibility */
INSERT #QA SELECT N'03. Domain',N'All feature values populated',COUNT_BIG(*)
FROM analytics.CustomerSnapshot
WHERE RecencyDays IS NULL OR Frequency IS NULL OR Monetary IS NULL
 OR OrdersLast90Days IS NULL OR OrdersLast180Days IS NULL
 OR Tenure IS NULL OR Share_Bikes IS NULL OR Share_Accessories IS NULL
 OR Share_Clothing IS NULL OR NSub IS NULL;
INSERT #QA SELECT N'03. Domain',N'RFM and time-window bounds valid',COUNT_BIG(*)
FROM analytics.CustomerSnapshot
WHERE Frequency<1 OR Monetary<0 OR RecencyDays<1
 OR Tenure<RecencyDays OR OrdersLast90Days<0 OR OrdersLast180Days<0
 OR OrdersLast90Days>OrdersLast180Days OR OrdersLast180Days>Frequency;
INSERT #QA SELECT N'03. Domain',N'Product shares and NSub within domain',COUNT_BIG(*)
FROM analytics.CustomerSnapshot
WHERE Share_Bikes NOT BETWEEN 0 AND 1
 OR Share_Accessories NOT BETWEEN 0 AND 1
 OR Share_Clothing NOT BETWEEN 0 AND 1
 OR Share_Bikes+Share_Accessories+Share_Clothing>1.000003
 OR NSub<0;
INSERT #QA SELECT N'03. Domain',N'Positive line-total denominator for all eligible customers',COUNT_BIG(*)
FROM #QHead h LEFT JOIN #QLines l
 ON l.CustomerID=h.CustomerID AND l.SnapshotDate=h.SnapshotDate
WHERE l.CustomerID IS NULL OR l.TotalLines<=0;

/* 04 Independent transaction-level metric reconciliation */
INSERT #QA SELECT N'04. RFM verification',N'Frequency equals recomputation from orders',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s JOIN #QHead h
 ON h.CustomerID=s.CustomerID AND h.SnapshotDate=s.SnapshotDate
WHERE s.Frequency<>h.ExpectedFrequency;
INSERT #QA SELECT N'04. RFM verification',N'Monetary=sum(TotalDue), tolerance 0.01',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s JOIN #QHead h
 ON h.CustomerID=s.CustomerID AND h.SnapshotDate=s.SnapshotDate
WHERE ABS(s.Monetary-h.ExpectedMonetary)>0.01;
INSERT #QA SELECT N'04. RFM verification',N'Recency from latest eligible OrderDate',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s JOIN #QHead h
 ON h.CustomerID=s.CustomerID AND h.SnapshotDate=s.SnapshotDate
WHERE s.RecencyDays<>h.ExpectedRecency;
INSERT #QA SELECT N'04. RFM verification',N'Tenure from earliest eligible OrderDate',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s JOIN #QHead h
 ON h.CustomerID=s.CustomerID AND h.SnapshotDate=s.SnapshotDate
WHERE s.Tenure<>h.ExpectedTenure;
INSERT #QA SELECT N'04. RFM verification',N'Orders90 and Orders180 independently recomputed',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s JOIN #QHead h
 ON h.CustomerID=s.CustomerID AND h.SnapshotDate=s.SnapshotDate
WHERE s.OrdersLast90Days<>h.ExpectedOrders90
 OR s.OrdersLast180Days<>h.ExpectedOrders180;

/* 05 Product-line metric reconciliation */
INSERT #QA SELECT N'05. Product verification',N'Share_Bikes matches share of all LineTotal',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s JOIN #QLines l
 ON l.CustomerID=s.CustomerID AND l.SnapshotDate=s.SnapshotDate
WHERE l.TotalLines>0
 AND ABS(s.Share_Bikes-CAST(l.Bikes/l.TotalLines AS DECIMAL(9,6)))>0.000001;
INSERT #QA SELECT N'05. Product verification',N'Share_Accessories matches share of all LineTotal',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s JOIN #QLines l
 ON l.CustomerID=s.CustomerID AND l.SnapshotDate=s.SnapshotDate
WHERE l.TotalLines>0
 AND ABS(s.Share_Accessories-CAST(l.Accessories/l.TotalLines AS DECIMAL(9,6)))>0.000001;
INSERT #QA SELECT N'05. Product verification',N'Share_Clothing matches share of all LineTotal',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s JOIN #QLines l
 ON l.CustomerID=s.CustomerID AND l.SnapshotDate=s.SnapshotDate
WHERE l.TotalLines>0
 AND ABS(s.Share_Clothing-CAST(l.Clothing/l.TotalLines AS DECIMAL(9,6)))>0.000001;
INSERT #QA SELECT N'05. Product verification',N'NSub matches distinct non-NULL SubcategoryID',COUNT_BIG(*)
FROM analytics.CustomerSnapshot s JOIN #QLines l
 ON l.CustomerID=s.CustomerID AND l.SnapshotDate=s.SnapshotDate
WHERE s.NSub<>l.ExpectedNSub;

/* Summary first; FAIL detail second, then evidence tables ready to screenshot. */
SELECT COUNT(*) AS TotalChecks,
       SUM(CASE WHEN FailedRows=0 THEN 1 ELSE 0 END) AS Passed,
       SUM(CASE WHEN FailedRows>0 THEN 1 ELSE 0 END) AS Failed
FROM #QA;
SELECT Category,CheckName,FailedRows,
       CASE WHEN FailedRows=0 THEN N'PASS' ELSE N'FAIL' END AS Result
FROM #QA ORDER BY Category,CheckName;

/* BANG 4.2: exactly 20 dates including DSS date. */
SELECT CONVERT(CHAR(10),SnapshotDate,103) AS SnapshotDate_DDMMYYYY,
       COUNT(*) AS CustomersWithPurchaseHistory,
       SUM(CASE WHEN Tenure IS NULL OR Share_Bikes IS NULL
                      OR Share_Accessories IS NULL OR Share_Clothing IS NULL
                      OR NSub IS NULL THEN 1 ELSE 0 END) AS IncompleteFeatureRows,
       CASE WHEN SnapshotDate=CONVERT(DATE,'20140708',112)
             THEN N'DSS scoring' ELSE N'Historical' END AS SnapshotRole
FROM analytics.CustomerSnapshot
GROUP BY SnapshotDate ORDER BY SnapshotDate;

/* Figure: show real feature values. */
SELECT TOP (20) SnapshotDate,CustomerID,RecencyDays,Frequency,Monetary,
       OrdersLast90Days,OrdersLast180Days,Tenure,
       Share_Bikes,Share_Accessories,Share_Clothing,NSub
FROM analytics.CustomerSnapshot
WHERE SnapshotDate=CONVERT(DATE,'20140708',112)
ORDER BY CustomerID;
GO
