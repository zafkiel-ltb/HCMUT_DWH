/* RESET_SCORES.sql - Xoá kết quả mô hình (cụm 5) để C3_01/C3_02 cho phép tính lại Snapshot.
   Thứ tự xoá theo khoá ngoại: CustomerRiskScore -> ModelTreeLeaf -> ModelRegistry.
   Không chạm Fact/Dim/Snapshot. Chỉ chạy khi thật sự cần tính lại Snapshot hoặc làm lại cụm 5 từ đầu. */
USE [CompanyX_DW];
SET NOCOUNT ON; SET XACT_ABORT ON;
BEGIN TRANSACTION;
  DECLARE @a INT = (SELECT COUNT(*) FROM analytics.CustomerRiskScore),
          @b INT = (SELECT COUNT(*) FROM analytics.ModelTreeLeaf),
          @c INT = (SELECT COUNT(*) FROM analytics.ModelRegistry);
  DELETE FROM analytics.CustomerRiskScore;
  DELETE FROM analytics.ModelTreeLeaf;
  DELETE FROM analytics.ModelRegistry;
COMMIT TRANSACTION;
PRINT CONCAT(N'Đã xoá: CustomerRiskScore ', @a, N', ModelTreeLeaf ', @b, N', ModelRegistry ', @c, N'. Snapshot giữ nguyên.');
SELECT COUNT(*) AS SnapshotRows FROM analytics.CustomerSnapshot;
