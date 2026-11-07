/* Thay the cho C2_02_Run_ETL_ONLY.py khi khong co Python/pyodbc.
   Chay trong SSMS hoac sqlcmd, database CompanyX_DW. Chi goi etl.usp_FullLoad. */
USE [CompanyX_DW];
SET NOCOUNT ON;
DECLARE @r UNIQUEIDENTIFIER = NEWID();
EXEC etl.usp_FullLoad @RunID=@r;
SELECT [Status],ErrorMessage FROM etl.RunLog WHERE RunID=@r;
SELECT StepNo,StepName,SourceRows,LoadedRows,ExcludedRows,RejectedRows FROM etl.StepLog WHERE RunID=@r ORDER BY StepNo;
SELECT EntityType,IsInScope,COUNT(*) AS N FROM etl.RejectedRow WHERE RunID=@r GROUP BY EntityType,IsInScope ORDER BY 1,2;
SELECT EntityType,RejectReason,COUNT(*) AS N FROM etl.RejectedRow WHERE RunID=@r GROUP BY EntityType,RejectReason ORDER BY 1,2;
