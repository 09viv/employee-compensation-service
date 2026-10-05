import pyodbc
import os
import re

CONN_STR_MASTER = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost,1433;"
    "Database=master;"
    "Uid=sa;"
    "Pwd=YourStrong!Passw0rd;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

def run_script(conn, filepath):
    print(f"Executing: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split on GO statements (case-insensitive on their own line)
    batches = re.split(r"^\s*GO\s*$", content, flags=re.MULTILINE | re.IGNORECASE)
    cursor = conn.cursor()
    for batch in batches:
        b = batch.strip()
        if b:
            cursor.execute(b)
    conn.commit()
    print(f"Finished: {filepath}")

def main():
    print("Connecting to SQL Server (master)...")
    conn = pyodbc.connect(CONN_STR_MASTER, autocommit=True)
    
    script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sql")
    
    # 01 create database
    run_script(conn, os.path.join(script_dir, "01_create_database.sql"))
    conn.close()

    # Now connect to EmployeeCompensation
    conn_db = pyodbc.connect(
        CONN_STR_MASTER.replace("Database=master;", "Database=EmployeeCompensation;"),
        autocommit=False
    )
    
    # 02 create tables
    run_script(conn_db, os.path.join(script_dir, "02_create_tables.sql"))
    
    # 03 seed data
    run_script(conn_db, os.path.join(script_dir, "03_seed_data.sql"))
    
    cursor = conn_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM dbo.Employee")
    emp_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM dbo.Department")
    dept_count = cursor.fetchone()[0]
    
    print(f"\nSUCCESS! Database seeded with {dept_count} departments and {emp_count} employees.")
    conn_db.close()

if __name__ == "__main__":
    main()
