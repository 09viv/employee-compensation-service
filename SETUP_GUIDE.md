# 🚀 Quick Start — Step-by-Step Action Guide

> Follow these steps **in order** to get the Employee Compensation Service running on your local machine.

---

## Step 1: Install Prerequisites

You need these tools installed before anything else.

### 1.1 — Install Python 3.9+

```bash
# Check if Python is already installed
python --version
```

If not installed, download from: https://www.python.org/downloads/  
✅ During installation, **check "Add Python to PATH"**.

### 1.2 — Install Azure Functions Core Tools v4

```bash
# Install via winget (recommended on Windows)
winget install Microsoft.Azure.FunctionsCoreTools --accept-package-agreements --accept-source-agreements
```

Alternative: Download the MSI installer from: https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local

> ⚠️ **Do NOT use `npm install -g azure-functions-core-tools@4`** — it has a known ESM compatibility issue with Node.js v20+.

Verify:
```bash
func --version
```

> 💡 **If `func` is still not recognized in your currently open terminal:**
> Windows terminals don't automatically refresh `PATH` for existing sessions. Either:
> 1. Run this in your terminal to refresh PATH immediately:
>    ```powershell
>    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
>    ```
> 2. Or kill the terminal (click the 🗑️ trash icon in the terminal panel) and open a new terminal.

### 1.3 — Install ODBC Driver 18 for SQL Server

Download and install from:  
https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

Just run the installer → Next → Next → Finish.

---

## Step 2: Set Up SQL Server

Pick **one** of these options:

### Option A — Docker (Easiest ✅)

Run these two containers (SQL Server and the local Azure Storage emulator):

```bash
# 1. Pull and start SQL Server
docker run -e "ACCEPT_EULA=Y" ^
           -e "MSSQL_SA_PASSWORD=YourStrong!Passw0rd" ^
           -p 1433:1433 ^
           --name sql-server ^
           -d mcr.microsoft.com/mssql/server:2022-latest

# 2. Start Azurite (local Azure storage emulator)
docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 ^
           --name azurite ^
           -d mcr.microsoft.com/azure-storage/azurite
```

```bash
# Verify both are running
docker ps
```

### Option B — Local SQL Server

If you already have SQL Server installed (Developer/Express edition), just make sure:
1. TCP/IP is enabled in SQL Server Configuration Manager
2. You know your `sa` password (or a login with admin rights)

---

## Step 3: Create the Database and Tables

Run these SQL scripts **in order**. You can use:
- **Python script (Automated & Easiest ✅)**
- **sqlcmd** (command line)
- **SSMS / Azure Data Studio**

### Option 1 — Using Python (Fastest & Automated ✅):

```bash
python run_migrations.py
```
*(This automatically connects to your local SQL Server and runs all 3 scripts in order!)*

### Option 2 — Using sqlcmd (from terminal):

```bash
# 3.1 — Create the database
sqlcmd -S localhost,1433 -U sa -P "YourStrong!Passw0rd" -C -i sql/01_create_database.sql
```

```bash
# 3.2 — Create tables
sqlcmd -S localhost,1433 -U sa -P "YourStrong!Passw0rd" -C -d EmployeeCompensation -i sql/02_create_tables.sql
```

```bash
# 3.3 — Insert sample data (12 employees, 5 departments)
sqlcmd -S localhost,1433 -U sa -P "YourStrong!Passw0rd" -C -d EmployeeCompensation -i sql/03_seed_data.sql
```
*(Note: `-C` trusts the server certificate and `,1433` routes directly to the Docker port).*

### Using SSMS or Azure Data Studio:

1. Connect to `localhost` with username `sa` and your password
2. Open `sql/01_create_database.sql` → press **F5** (Execute)
3. Open `sql/02_create_tables.sql` → press **F5**
4. Open `sql/03_seed_data.sql` → press **F5**

✅ You should see "Seed data inserted successfully."

---

## Step 4: Set Up the Python Project

Open a terminal in the project folder:

```bash
cd employee-compensation-service
```

### 4.1 — Create a virtual environment

```bash
python -m venv .venv
```

### 4.2 — Activate it

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat
```

### 4.3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

## Step 5: Configure the Connection String

Open `local.settings.json` and update the `SQL_CONNECTION_STRING` with your actual password:

```json
{
    "IsEncrypted": false,
    "Values": {
        "AzureWebJobsStorage": "UseDevelopmentStorage=true",
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "SQL_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=localhost,1433;Database=EmployeeCompensation;Uid=sa;Pwd=YourStrong!Passw0rd;Encrypt=yes;TrustServerCertificate=yes;",
        "APPLY_DEFAULT_BONUS": "false"
    }
}
```

⚠️ Replace `YourStrong!Passw0rd` with your actual SQL Server password.

> 💡 **Important for Windows & Docker:** Always specify `,1433` (e.g. `Server=localhost,1433`). If you omit `,1433`, Windows ODBC attempts Shared Memory / Named Pipes to the host's native Windows SQL Server instance (if installed) instead of your Docker container, causing `Login failed for user 'sa'` (18456) and HTTP 500 errors.

---

## Step 6: Run the Service

```bash
func start
```

You should see output like:
```
Functions:

        create_employee: [POST] http://localhost:7071/api/employees
        get_employee:    [GET]  http://localhost:7071/api/employees/{employee_id}
        list_employees:  [GET]  http://localhost:7071/api/employees
        update_employee: [PUT]  http://localhost:7071/api/employees/{employee_id}
        delete_employee: [DELETE] http://localhost:7071/api/employees/{employee_id}
        report_total_bonus:          [GET] http://localhost:7071/api/reports/total-bonus
        report_no_bonus:             [GET] http://localhost:7071/api/reports/no-bonus
        report_bonus_percentage:     [GET] http://localhost:7071/api/reports/bonus-percentage
        report_departments_high_bonus: [GET] http://localhost:7071/api/reports/departments-high-bonus
        report_bonus_ranking:        [GET] http://localhost:7071/api/reports/bonus-ranking
        report_highest_salary:       [GET] http://localhost:7071/api/reports/highest-salary
```

✅ The service is now running at **http://localhost:7071/api/**

---

## Step 7: Test the Endpoints

Open a **new terminal** (keep the service running in the first one).

> 💡 **Windows PowerShell Tip:** In PowerShell, `curl` is an alias for `Invoke-WebRequest`. Use `curl.exe` or `Invoke-RestMethod` to get direct JSON output.

### Test CRUD Operations

```bash
# List all employees
curl.exe http://localhost:7071/api/employees

# Get a single employee
curl.exe http://localhost:7071/api/employees/1

# List employees in department 3 (Sales)
curl.exe "http://localhost:7071/api/employees?departmentId=3"

# Create a new employee
curl.exe -X POST http://localhost:7071/api/employees -H "Content-Type: application/json" -d "{\"firstName\":\"Vivek\",\"lastName\":\"Test\",\"departmentId\":1,\"salary\":100000,\"hireDate\":\"2024-01-15\"}"

# Update an employee's bonus
curl.exe -X PUT http://localhost:7071/api/employees/1 -H "Content-Type: application/json" -d "{\"bonus\": 30000}"

# Delete an employee
curl.exe -X DELETE http://localhost:7071/api/employees/2
```

### Test Report Endpoints

```bash
# Total bonus across the company
curl.exe http://localhost:7071/api/reports/total-bonus

# Employees with no bonus
curl.exe http://localhost:7071/api/reports/no-bonus

# Bonus as percentage of salary
curl.exe http://localhost:7071/api/reports/bonus-percentage

# Departments where total bonus > average salary
curl.exe http://localhost:7071/api/reports/departments-high-bonus

# Employees ranked by bonus (NULL last)
curl.exe http://localhost:7071/api/reports/bonus-ranking

# Highest salary analysis
curl.exe http://localhost:7071/api/reports/highest-salary
```

---

## Step 8 (Optional): Enable Default Bonus Feature

To apply a default 5% bonus for employees who don't have one, change this in `local.settings.json`:

```json
"APPLY_DEFAULT_BONUS": "true"
```

Then restart the service (`Ctrl+C` → `func start`).

Now when you call `GET /api/employees/2` (Bob Smith, who has no bonus, salary = 115,000):
- **Before**: `"bonus": null`
- **After**: `"bonus": 5750.00` (5% of 115,000, calculated at read-time)

---

## 🛑 Troubleshooting

| Problem | Fix |
|---------|-----|
| `func` command not found | Install Azure Functions Core Tools (Step 1.2) |
| `pyodbc.Error: Can't open lib 'ODBC Driver 18'` | Install ODBC Driver 18 (Step 1.3) |
| `Connection refused` on port 1433 | Make sure SQL Server / Docker container is running |
| `Login failed for user 'sa'` (18456) or HTTP 500 | Ensure `Server=localhost,1433` specifies `,1433` in `local.settings.json`. Omission connects to local Windows SQL Server via Shared Memory instead of Docker. |
| `Invalid object name 'dbo.Employee'` | Run the SQL scripts (Step 3) |
| `ModuleNotFoundError: No module named 'pyodbc'` | Activate venv and run `pip install -r requirements.txt` |
| `func start` shows no functions | Make sure you're in the `employee-compensation-service/` directory |
| Changes in `local.settings.json` not taking effect | Restart `func start` (`Ctrl+C` then `func start`) |

---

## 📋 Quick Reference — All Endpoints

| # | Method | URL | What It Does |
|---|--------|-----|--------------|
| 1 | `POST` | `/api/employees` | Create employee |
| 2 | `GET` | `/api/employees/{id}` | Get employee by ID |
| 3 | `GET` | `/api/employees?departmentId=N` | List employees |
| 4 | `PUT` | `/api/employees/{id}` | Update employee |
| 5 | `DELETE` | `/api/employees/{id}` | Delete employee |
| 6 | `GET` | `/api/reports/total-bonus` | Total company bonus |
| 7 | `GET` | `/api/reports/no-bonus` | Employees without bonus |
| 8 | `GET` | `/api/reports/bonus-percentage` | Bonus as % of salary |
| 9 | `GET` | `/api/reports/departments-high-bonus` | Depts: bonus > avg salary |
| 10 | `GET` | `/api/reports/bonus-ranking` | Ranked by bonus |
| 11 | `GET` | `/api/reports/highest-salary` | Highest salary analysis |
