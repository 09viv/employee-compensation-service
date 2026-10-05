# Employee Compensation Service

> Azure Functions (Python v2) HTTP API backed by SQL Server for managing employee records and compensation reporting.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start Scripts (Automated)](#quick-start-scripts-automated)
- [Local Installation](#local-installation)
  - [Automated Setup Script](#automated-setup-script)
  - [Manual Step-by-Step Installation](#manual-step-by-step-installation)
- [Database Configuration & Setup](#database-configuration--setup)
  - [Option A — Docker (Recommended for Quick Setup)](#option-a--docker-recommended-for-quick-setup)
  - [Option B — Local SQL Server](#option-b--local-sql-server)
  - [Option C — Azure SQL Database](#option-c--azure-sql-database)
  - [Running the Database Migrations & Seed Data](#running-the-database-migrations--seed-data)
- [Configuration](#configuration)
- [Process of Execution](#process-of-execution)
  - [Execution Workflow Overview](#execution-workflow-overview)
  - [Step 1: Start SQL Server & Azurite](#step-1-start-sql-server--azurite)
  - [Step 2: Run Database Migrations](#step-2-run-database-migrations)
  - [Step 3: Launch Azure Functions Host](#step-3-launch-azure-functions-host)
  - [Step 4: Verify & Test Execution](#step-4-verify--test-execution)
  - [Step 5: Stopping the Service](#step-5-stopping-the-service)
- [API Endpoints](#api-endpoints)
- [Design Decisions](#design-decisions)
- [Project Structure](#project-structure)

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.9+ | Application runtime |
| **Azure Functions Core Tools** | v4.x | Local serverless host (`func`) |
| **ODBC Driver 18 for SQL Server** | Latest | Database connectivity (`pyodbc`) |
| **SQL Server** | 2019+ (or Azure SQL / Docker) | Database engine |
| **Azurite** *(optional)* | Latest | Local Azure storage emulator |

### Installing ODBC Driver 18

**Windows:**
Download and run the official installer from [Microsoft ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server).

**macOS (Homebrew):**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18
```

**Ubuntu / Debian:**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### Installing Azure Functions Core Tools v4

**Windows (PowerShell / winget):**
```powershell
winget install Microsoft.Azure.FunctionsCoreTools --accept-package-agreements --accept-source-agreements
```
> *Note: Refresh your environment or restart terminal after install so `func` is in PATH.*

**macOS (Homebrew):**
```bash
brew tap azure/azure-functions
brew install azure-functions-core-tools@4
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/microsoft-ubuntu-$(lsb_release -cs)-prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

---

## Quick Start Scripts (Automated)

The repository provides ready-to-run automation scripts for both installation and execution:

### Windows (PowerShell)
```powershell
# 1. Run local installation & dependencies setup
.\setup.ps1

# 2. Run database migrations & seed data (once database is running)
python run_migrations.py

# 3. Start the service
.\start.ps1
```

### macOS / Linux (Bash)
```bash
# 1. Make scripts executable and run installation
chmod +x setup.sh start.sh
./setup.sh

# 2. Run database migrations & seed data (once database is running)
python run_migrations.py

# 3. Start the service
./start.sh
```

---

## Local Installation

### Automated Setup Script

Run the automated setup script to automatically create `.venv`, install packages from `requirements.txt`, configure `local.settings.json`, and check for runtime tools:

- **Windows:** `.\setup.ps1`
- **Linux/macOS:** `./setup.sh`

### Manual Step-by-Step Installation

If you prefer to configure your environment manually, follow the script below:

#### Windows (PowerShell)

```powershell
# 1. Clone the repository and enter the directory
git clone <repository-url>
cd employee-compensation-service

# 2. Create Python virtual environment
python -m venv .venv

# 3. Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Initialize local configuration file
if (-not (Test-Path "local.settings.json")) {
    Copy-Item "local.settings.example.json" "local.settings.json"
}
```

#### macOS / Linux (Bash)

```bash
# 1. Clone the repository and enter the directory
git clone <repository-url>
cd employee-compensation-service

# 2. Create Python virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Initialize local configuration file
if [ ! -f "local.settings.json" ]; then
    cp local.settings.example.json local.settings.json
fi
```

---

## Database Configuration & Setup

Choose one of the database options below:

### Option A — Docker (Recommended for Quick Setup)

Run SQL Server and Azurite containers:

**Windows (PowerShell) / macOS / Linux:**
```bash
# 1. Start SQL Server 2022 container
docker run -e "ACCEPT_EULA=Y" `
           -e "MSSQL_SA_PASSWORD=YourStrong!Passw0rd" `
           -p 1433:1433 `
           --name sql-server `
           -d mcr.microsoft.com/mssql/server:2022-latest

# 2. Start Azurite storage emulator
docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 `
           --name azurite `
           -d mcr.microsoft.com/azure-storage/azurite

# 3. Verify containers are running
docker ps
```

Connection string for Docker:
```
Driver={ODBC Driver 18 for SQL Server};Server=localhost,1433;Database=EmployeeCompensation;Uid=sa;Pwd=YourStrong!Passw0rd;Encrypt=yes;TrustServerCertificate=yes;
```

### Option B — Local SQL Server

1. **Install SQL Server** (Developer or Express Edition):
   - Enable **Mixed Mode Authentication** and set an `sa` password during setup.
2. **Enable TCP/IP in SQL Server Configuration Manager**:
   - Navigate to **SQL Server Network Configuration → Protocols for MSSQLSERVER**.
   - Enable **TCP/IP** and restart the SQL Server service.
3. **Connection string:**
   ```
   Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=EmployeeCompensation;Uid=sa;Pwd=YourPassword;Encrypt=yes;TrustServerCertificate=yes;
   ```

### Option C — Azure SQL Database

1. Create a SQL Database resource in the **Azure Portal**.
2. Configure **Networking / Firewall** to allow your local client IP.
3. Connection string:
   ```
   Driver={ODBC Driver 18 for SQL Server};Server=tcp:YOUR_SERVER.database.windows.net,1433;Database=EmployeeCompensation;Uid=YOUR_USER;Pwd=YOUR_PASSWORD;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
   ```

### Running the Database Migrations & Seed Data

Execute the database migration to create `EmployeeCompensation`, schemas, tables, constraints, indexes, and seed records (12 employees, 5 departments).

#### Method 1: Automated Python Runner (Recommended ✅)
Make sure your virtual environment is active and run:
```bash
python run_migrations.py
```
*This executes `sql/01_create_database.sql`, `sql/02_create_tables.sql`, and `sql/03_seed_data.sql` sequentially and validates table counts.*

#### Method 2: Command-Line (`sqlcmd`)
```bash
# 1. Create database (connect to master)
sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -i sql/01_create_database.sql

# 2. Create tables
sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -d EmployeeCompensation -i sql/02_create_tables.sql

# 3. Seed sample data
sqlcmd -S localhost -U sa -P "YourStrong!Passw0rd" -d EmployeeCompensation -i sql/03_seed_data.sql
```

#### Method 3: SSMS / Azure Data Studio
Open and execute each file in order:
1. `sql/01_create_database.sql`
2. `sql/02_create_tables.sql`
3. `sql/03_seed_data.sql`

---

## Configuration

All runtime configurations are read from environment variables (provided locally by `local.settings.json`).

| Variable | Required | Description |
|----------|----------|-------------|
| `SQL_CONNECTION_STRING` | ✅ | Full ODBC connection string to SQL Server |
| `APPLY_DEFAULT_BONUS` | ❌ | Set to `"true"` to apply a default 5% bonus at read-time for employees without bonus. Default: `"false"` |
| `AzureWebJobsStorage` | ✅ | Azure WebJobs storage connection string (`UseDevelopmentStorage=true` for local Azurite) |

Verify your `local.settings.json`:
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

> ⚠️ **`local.settings.json` is listed in `.gitignore` and must never be committed to source control.**

---

## Process of Execution

Follow this sequential workflow to run and verify the service:

### Execution Workflow Overview

```
[Start Database / Docker] ➔ [Run Migrations / Seed Data] ➔ [Start Function Host] ➔ [Verify via HTTP]
```

### Step 1: Start SQL Server & Azurite

- **If using Docker containers created previously:**
  ```bash
  docker start sql-server azurite
  ```
- **If using Windows Local SQL Server Service:**
  ```powershell
  # Check status and start if stopped
  Get-Service -Name MSSQLSERVER | Start-Service
  ```

### Step 2: Run Database Migrations

Apply the database schema and seed data (only required once or on database reset):
```bash
python run_migrations.py
```
Output:
```text
Connecting to SQL Server (master)...
Executing: .../sql/01_create_database.sql
Executing: .../sql/02_create_tables.sql
Executing: .../sql/03_seed_data.sql

SUCCESS! Database seeded with 5 departments and 12 employees.
```

### Step 3: Launch Azure Functions Host

Activate the virtual environment and start the Functions host:

- **Option A — Using convenience script:**
  - Windows: `.\start.ps1`
  - Linux/macOS: `./start.sh`

- **Option B — Using Azure Functions Core Tools CLI:**
  ```bash
  # Windows PowerShell
  .\.venv\Scripts\Activate.ps1
  func start

  # Linux / macOS
  source .venv/bin/activate
  func start
  ```

Once started, the Functions host displays the available HTTP routes:
```text
Functions:
    create_employee:             [POST]   http://localhost:7071/api/employees
    get_employee:                [GET]    http://localhost:7071/api/employees/{employee_id}
    list_employees:              [GET]    http://localhost:7071/api/employees
    update_employee:             [PUT]    http://localhost:7071/api/employees/{employee_id}
    delete_employee:             [DELETE] http://localhost:7071/api/employees/{employee_id}
    report_total_bonus:          [GET]    http://localhost:7071/api/reports/total-bonus
    report_no_bonus:             [GET]    http://localhost:7071/api/reports/no-bonus
    report_bonus_percentage:     [GET]    http://localhost:7071/api/reports/bonus-percentage
    report_departments_high_bonus: [GET]  http://localhost:7071/api/reports/departments-high-bonus
    report_bonus_ranking:        [GET]    http://localhost:7071/api/reports/bonus-ranking
    report_highest_salary:       [GET]    http://localhost:7071/api/reports/highest-salary
```

### Step 4: Verify & Test Execution

Open a separate terminal window and test the running service:

#### Using PowerShell:
```powershell
# 1. Fetch employee list
Invoke-RestMethod -Uri "http://localhost:7071/api/employees" -Method Get | ConvertTo-Json -Depth 3

# 2. Fetch total bonus report
Invoke-RestMethod -Uri "http://localhost:7071/api/reports/total-bonus" -Method Get | ConvertTo-Json

# 3. Create a new employee
$body = @{
    firstName    = "Jane"
    lastName     = "Doe"
    departmentId = 1
    salary       = 95000.00
    bonus        = 12000.00
    hireDate     = "2023-01-15"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:7071/api/employees" -Method Post -Body $body -ContentType "application/json"
```

#### Using cURL (Bash / macOS / Linux / CMD):
```bash
# 1. Fetch employee list
curl -s http://localhost:7071/api/employees

# 2. Fetch total bonus report
curl -s http://localhost:7071/api/reports/total-bonus

# 3. Create a new employee
curl -X POST http://localhost:7071/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Jane",
    "lastName": "Doe",
    "departmentId": 1,
    "salary": 95000.00,
    "bonus": 12000.00,
    "hireDate": "2023-01-15"
  }'
```

### Step 5: Stopping the Service

To terminate the running Azure Functions host:
- Press `Ctrl + C` in the terminal running `func start`.
- (Optional) If using Docker, stop containers when finished:
  ```bash
  docker stop sql-server azurite
  ```

---

## API Endpoints

### Part A — CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/employees` | Create a new employee |
| `GET` | `/api/employees/{id}` | Get employee by ID |
| `GET` | `/api/employees?departmentId=N` | List employees (optional filter) |
| `PUT` | `/api/employees/{id}` | Update an employee |
| `DELETE` | `/api/employees/{id}` | Delete an employee |

### Part B — Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/reports/total-bonus` | Total bonus across the company |
| `GET` | `/api/reports/no-bonus` | Employees without a bonus |
| `GET` | `/api/reports/bonus-percentage` | Bonus as % of salary |
| `GET` | `/api/reports/departments-high-bonus` | Departments where bonus > avg salary |
| `GET` | `/api/reports/bonus-ranking` | Employees ranked by bonus |
| `GET` | `/api/reports/highest-salary` | Highest salary analysis |

### Example Requests

**Create an employee:**
```bash
curl -X POST http://localhost:7071/api/employees \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Alice",
    "lastName": "Johnson",
    "departmentId": 1,
    "salary": 130000.00,
    "bonus": 26000.00,
    "hireDate": "2019-03-15"
  }'
```

**List employees in department 3:**
```bash
curl http://localhost:7071/api/employees?departmentId=3
```

**Update an employee's bonus:**
```bash
curl -X PUT http://localhost:7071/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{ "bonus": 30000.00 }'
```

**Clear an employee's bonus (set to NULL):**
```bash
curl -X PUT http://localhost:7071/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{ "clearBonus": true }'
```

---

## Design Decisions

### Default Bonus (Part C — Optional Feature)

**Decision: Read-time calculation (not write-time).**

When `APPLY_DEFAULT_BONUS=true`, employees with `Bonus IS NULL` will have a calculated default of **5% of their salary** in API responses. The database value remains `NULL`.

**Rationale:**
- **Data integrity**: The original fact — "this employee was not awarded a bonus" — is preserved in the database.
- **Reversibility**: Turning the feature off immediately stops showing defaults; no data migration needed.
- **Auditability**: Reports that distinguish between "no bonus" and "default bonus" can still query the raw `NULL` value.
- **No side effects**: Write-time mutation would permanently overwrite `NULL`, losing the distinction.

### Error Handling

- `400` — Malformed request body, invalid parameters, validation errors
- `404` — Employee or resource not found
- `409` — Conflict (e.g., FK constraint violation)
- `500` — Unexpected server errors (details logged, not exposed to client)

---

## Project Structure

```
employee-compensation-service/
├── function_app.py              # Azure Functions entry point (all routes)
├── host.json                    # Functions host configuration
├── local.settings.json          # Local env vars (gitignored)
├── requirements.txt             # Python dependencies
├── .gitignore
│
├── models/
│   ├── __init__.py
│   └── schemas.py               # Pydantic request/response models
│
├── services/
│   ├── __init__.py
│   ├── database.py              # Connection pool & query helpers
│   ├── employee_service.py      # CRUD business logic
│   └── report_service.py        # Reporting queries (Part B)
│
├── utils/
│   ├── __init__.py
│   └── responses.py             # HTTP response helpers
│
└── sql/
    ├── 01_create_database.sql   # Database creation
    ├── 02_create_tables.sql     # DDL + constraints + indexes
    └── 03_seed_data.sql         # Sample data (12 employees, 5 depts)
```
