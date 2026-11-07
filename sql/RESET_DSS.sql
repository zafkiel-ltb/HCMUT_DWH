/* RESET_DSS.sql – Xoá kết quả cụm 6 (khuyến nghị, phân nhóm, quy tắc, đăng ký K-means) để chạy lại CUM6_01..03. Không chạm điểm rủi ro. */
USE [CompanyX_DW];
SET NOCOUNT ON; SET XACT_ABORT ON; SET QUOTED_IDENTIFIER ON;
BEGIN TRANSACTION;
DELETE FROM analytics.CareRecommendation; DELETE FROM analytics.CustomerSegment; DELETE FROM analytics.CareRule;
DELETE FROM analytics.ModelRegistry WHERE ModelRole=N'CLUSTERING';
COMMIT TRANSACTION;
PRINT N'Đã xoá kết quả cụm 6. Điểm rủi ro và Snapshot giữ nguyên.';
