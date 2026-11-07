SET NOCOUNT ON;
:OUT /tmp/run/x_snapshot.csv
SELECT CustomerID,CONVERT(VARCHAR(10),SnapshotDate,120) T,CustomerKey,RecencyDays,Frequency,Monetary,OrdersLast90Days,OrdersLast180Days,Tenure,Share_Bikes,Share_Accessories,Share_Clothing,NSub FROM analytics.CustomerSnapshot ORDER BY SnapshotDate,CustomerID;
:OUT /tmp/run/x_orders.csv
SELECT f.SalesOrderID,c.CustomerID,CONVERT(VARCHAR(10),d.FullDate,120) OrderDate,CONVERT(VARCHAR(10),f.ShipDate,120) ShipDate,f.SubTotal,f.TaxAmt,f.Freight,f.TotalDue,t.TerritoryID FROM dbo.FactSalesOrder f JOIN dbo.DimCustomer c ON c.CustomerKey=f.CustomerKey JOIN dbo.DimDate d ON d.DateKey=f.OrderDateKey LEFT JOIN dbo.DimTerritory t ON t.TerritoryKey=f.TerritoryKey ORDER BY f.SalesOrderID;
:OUT /tmp/run/x_lines.csv
SELECT l.SalesOrderID,l.SalesOrderDetailID,p.ProductID,p.CategoryName,p.SubcategoryName,l.OrderQty,l.UnitPrice,l.UnitPriceDiscount,l.LineTotal FROM dbo.FactSalesOrderLine l JOIN dbo.DimProduct p ON p.ProductKey=l.ProductKey ORDER BY 1,2;
:OUT /tmp/run/x_cost.csv
SELECT d.SalesOrderID,d.SalesOrderDetailID,d.ProductID,d.OrderQty,ISNULL(h.StandardCost,p.StandardCost) StandardCost FROM CompanyX.Sales.SalesOrderDetail d JOIN CompanyX.Sales.SalesOrderHeader o ON o.SalesOrderID=d.SalesOrderID JOIN CompanyX.Production.Product p ON p.ProductID=d.ProductID LEFT JOIN CompanyX.Production.ProductCostHistory h ON h.ProductID=d.ProductID AND o.OrderDate>=h.StartDate AND (h.EndDate IS NULL OR o.OrderDate<h.EndDate) ORDER BY 1,2;
:OUT /tmp/run/x_customers.csv
SELECT CustomerID,CustomerKey,SourceTerritoryID FROM dbo.DimCustomer ORDER BY 1;
