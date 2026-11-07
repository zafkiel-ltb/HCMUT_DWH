"""Run Cluster 2 full-load only, without rebuilding old CustomerSnapshot.

  Windows Command Prompt: py C2_02_Run_ETL_ONLY.py
  Environment SQL_SERVER / SQL_DRIVER if not using localhost / ODBC Driver 18.
  This script calls only etl.usp_FullLoad; it NEVER calls etl.usp_RebuildSnapshots.
"""
import os
import uuid
from pathlib import Path
import csv
import pyodbc

SERVER = os.getenv("SQL_SERVER", "localhost")
DRIVER = os.getenv("SQL_DRIVER", "ODBC Driver 18 for SQL Server")
DATABASE = "CompanyX_DW"
RUN_ID = str(uuid.uuid4())
CONNECTION = (
    f"DRIVER={{{DRIVER}}};SERVER={SERVER};DATABASE={DATABASE};"
    "Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=yes;"
)


def fetch(conn, sql, *params):
    cur = conn.cursor()
    try:
        cur.execute(sql, *params)
        return [tuple(r) for r in cur.fetchall()]
    finally:
        cur.close()


def main():
    print(f"Connected target: {SERVER}/{DATABASE}")
    print(f"ETL run ID: {RUN_ID}")
    print("IMPORTANT: only loads dimensions/facts; old snapshots are NOT rebuilt.")
    try:
        with pyodbc.connect(CONNECTION, autocommit=True, timeout=30) as conn:
            cur = conn.cursor()
            try:
                cur.execute("EXEC etl.usp_FullLoad @RunID=?", RUN_ID)
                while cur.nextset():
                    pass
            finally:
                cur.close()

            run = fetch(conn,
                "SELECT [Status],ErrorMessage FROM etl.RunLog WHERE RunID=?", RUN_ID)
            status, error = run[0] if run else ("NO RUN", "No RunLog record")
            print("Run status:", status)
            if status != "SUCCESS":
                raise RuntimeError(f"ETL did not succeed: {error}")

            steps = fetch(conn, """
                SELECT StepNo,StepName,SourceRows,LoadedRows,ExcludedRows,RejectedRows
                FROM etl.StepLog WHERE RunID=? ORDER BY StepNo
            """, RUN_ID)
            print("Step | Name | Read | Loaded | Excluded | Rejected(in-scope)")
            for s in steps:
                print(" | ".join(str(x) for x in s))
            audit = fetch(conn, """
                SELECT EntityType,IsInScope,COUNT(*)
                FROM etl.RejectedRow WHERE RunID=?
                GROUP BY EntityType,IsInScope ORDER BY EntityType,IsInScope
            """, RUN_ID)
            print("RejectedRow QUALITY LOG by scope (out-of-scope=0, in-scope=1):")
            for s in audit:
                print(" | ".join(str(x) for x in s))
            sample = fetch(conn, """
                SELECT TOP (20) EntityType,SourceKey,RejectReason,IsInScope
                FROM etl.RejectedRow WHERE RunID=?
                ORDER BY RejectID
            """, RUN_ID)
            for s in sample:
                print(" | ".join(str(x) for x in s))
            csv_path = Path(__file__).with_name(f"C2_ETL_steps_{RUN_ID[:8]}.csv")
            with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["StepNo","StepName","SourceRows","LoadedRows",
                                 "ExcludedRows","RejectedRowsInScope"])
                writer.writerows(steps)
            print("Audit CSV:", csv_path)
            print("Next: C2_03_Verify_and_Quality.sql in SSMS.")
    except (pyodbc.Error, RuntimeError) as exc:
        print("ERROR:", exc)
        print("Check etl.RunLog.ErrorMessage in SSMS and do not use stale snapshots as new ML input.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
