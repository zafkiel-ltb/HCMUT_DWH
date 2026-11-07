"""Cấu hình kết nối dùng chung cho mọi script Python của cụm 3B–6.
Đọc từ biến môi trường để cùng một mã chạy được trên Windows (Windows Authentication) và macOS/Linux (SQL login).

Windows (PowerShell):   $env:SQL_SERVER="localhost"             # mặc định Trusted_Connection
macOS (SQL login):      export SQL_SERVER=localhost,1433 SQL_USER=sa SQL_PASSWORD=...  (không ghi mật khẩu vào mã)
"""
import os

SQL_SERVER = os.getenv("SQL_SERVER", "localhost")
SQL_DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
SQL_USER = os.getenv("SQL_USER")           # None -> Windows Authentication
SQL_PASSWORD = os.getenv("SQL_PASSWORD")
DW_DATABASE = os.getenv("DW_DATABASE", "CompanyX_DW")
SOURCE_DATABASE = os.getenv("SOURCE_DATABASE", "CompanyX")

def connection_string(database: str = DW_DATABASE) -> str:
    base = f"DRIVER={{{SQL_DRIVER}}};SERVER={SQL_SERVER};DATABASE={database};Encrypt=yes;TrustServerCertificate=yes;"
    if SQL_USER:
        return base + f"UID={SQL_USER};PWD={SQL_PASSWORD};"
    return base + "Trusted_Connection=yes;"

def connect(database: str = DW_DATABASE, autocommit: bool = False):
    """pyodbc đặt QUOTED_IDENTIFIER ON và ANSI_NULLS ON sẵn, cần cho filtered index trên analytics.ModelRegistry."""
    import pyodbc
    return pyodbc.connect(connection_string(database), autocommit=autocommit, timeout=30)

# Tham số thiết kế cố định (Chương 3). Không sửa ở đây, sửa ở Doc trước rồi mới đổi mã.
LABEL_DAYS = 90
LABEL_LAG_DAYS = 97                      # T + 97 <= E
LABEL_WINDOW_MUST_END_BEFORE = "2014-06-01"
FOLDS = [("2013-12-15", "2013-09-01"), ("2014-01-15", "2013-10-01"), ("2014-02-15", "2013-11-01"), ("2014-03-01", "2013-11-15")]  # (E, T) Bảng 3.12
SCORING_DATE, SCORING_TRAIN_DATE = "2014-07-08", "2014-03-01"
FEATURES = ["Recency", "Frequency", "Monetary", "Orders90", "Orders180", "Tenure", "Share_Bikes", "Share_Accessories", "Share_Clothing", "BikeBuyer", "NSub"]  # Bảng 3.9 + BikeBuyer (Bảng 3.10)
RECENCY_BINS = [-1, 89, 179, 269, 364, 539, 10**6]   # Bảng 3.10
FREQUENCY_BINS = [0, 1, 2, 10**6]
NSUB_BINS = [-1, 1, 2, 4, 10**6]
RISK_HIGH_PERCENTILE = 75                 # RiskLevel 'Cao' khi RiskPercentile >= 75, phân vị tính TRONG TỪNG HẠNG ABC (3.4.6, 3.5.3)
TREE_FLAG_GAP = 0.30                      # cờ xem xét khi |TreeScore - RiskScore| > 0,3
BASE_SCENARIO = dict(r=0.10, c=10.0, B=40000.0)   # kịch bản cơ sở 3.5.4
CHANNELS = {"R3": dict(cost=25.0, success=0.15), "R4": dict(cost=15.0, success=0.12), "R5": dict(cost=3.0, success=0.05)}  # Bảng 3.26a
GROSS_MARGIN = 0.4115                     # g tính từ ProductCostHistory tại ngày đặt (biên bản chuẩn hoá), Chương 4 trình bày căn cứ
RANDOM_STATE = 0
