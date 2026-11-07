/* PRE-FLIGHT, READ ONLY. Run this before installing the revised procedure. */
USE [CompanyX_DW];
GO
SET NOCOUNT ON;
SELECT DB_NAME() AS TargetDatabase,
       IIF(COL_LENGTH(N'etl.RejectedRow',N'IsInScope') IS NOT NULL, 'READY','MISSING') AS IsInScopeFlag,
       (SELECT COUNT(*) FROM dbo.FactSalesOrder) AS Orders_Before,
       (SELECT COUNT(*) FROM dbo.FactSalesOrderLine) AS Lines_Before,
       (SELECT COUNT(*) FROM analytics.CustomerSnapshot) AS Snapshots_Before;

/* Source-backed promotion semantics: confirm SpecialOfferID=1 means no discount. */
SELECT SpecialOfferID,[Description],DiscountPct,[Type]
FROM CompanyX.Sales.SpecialOffer
WHERE SpecialOfferID=1;

/* Preview both new GLOBAL validation rules, before scope filtering.
   Excludes legitimate promotional unit-price zero where SpecialOfferID<>1. */
;WITH Q AS (
 SELECT o.SalesOrderID,o.CustomerID,o.Status,o.SubTotal,
        CASE WHEN o.Status=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
             THEN 1 ELSE 0 END AS IsInScope,
        CASE WHEN o.SubTotal<=0 AND EXISTS (
             SELECT 1 FROM CompanyX.Sales.SalesOrderDetail l
             WHERE l.SalesOrderID=o.SalesOrderID) THEN 1 ELSE 0 END AS NonpositiveSubtotal
 FROM CompanyX.Sales.SalesOrderHeader o
 LEFT JOIN CompanyX.Sales.Customer c ON c.CustomerID=o.CustomerID
)
SELECT SalesOrderID,CustomerID,Status,SubTotal,IsInScope
FROM Q WHERE NonpositiveSubtotal=1 ORDER BY SalesOrderID;

SELECT TOP (100) l.SalesOrderID,l.SalesOrderDetailID,l.ProductID,
       l.UnitPrice,p.ListPrice,l.SpecialOfferID,o.Status,
       CASE WHEN o.Status=5 AND c.PersonID IS NOT NULL AND c.StoreID IS NULL
            THEN 1 ELSE 0 END AS IsInScope
FROM CompanyX.Sales.SalesOrderDetail l
JOIN CompanyX.Sales.SalesOrderHeader o ON o.SalesOrderID=l.SalesOrderID
LEFT JOIN CompanyX.Sales.Customer c ON c.CustomerID=o.CustomerID
JOIN CompanyX.Production.Product p ON p.ProductID=l.ProductID
WHERE l.UnitPrice=0 AND p.ListPrice>0 AND l.SpecialOfferID=1
ORDER BY l.SalesOrderID,l.SalesOrderDetailID;
GO
