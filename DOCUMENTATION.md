# Employee Compensation Service — Technical Documentation

> In-depth technical documentation covering architecture, data model, API contracts, SQL query design, error handling strategy, and deployment considerations.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Data Model](#2-data-model)
3. [API Reference](#3-api-reference)
   - [Part A — CRUD Endpoints](#part-a--crud-endpoints)
   - [Part B — Reporting Endpoints](#part-b--reporting-endpoints)
4. [SQL Query Design](#4-sql-query-design)
5. [Error Handling Strategy](#5-error-handling-strategy)
6. [Security & Secrets Management](#6-security--secrets-management)
7. [Default Bonus Feature (Part C)](#7-default-bonus-feature-part-c)
8. [Testing Guide](#8-testing-guide)
9. [Deployment to Azure](#9-deployment-to-azure)
10. [Known Assumptions](#10-known-assumptions)

---

## 1. Architecture Overview

```
┌──────────────┐     HTTP      ┌──────────────────────┐     ODBC     ┌──────────────┐
│   Clients    │ ────────────► │  Azure Functions v4   │ ───────────► │  SQL Server  │
│  (REST API)  │ ◄──────────── │  Python v2 Model      │ ◄─────────── │  Database    │
└──────────────┘    JSON       └──────────────────────┘              └──────────────┘
                                        │
                               ┌────────┴─────────┐
                               │   Layers          │
                               ├───────────────────┤
                               │ function_app.py   │  ← Route handlers (thin)
                               │ services/         │  ← Business logic + SQL
                               │ models/           │  ← Pydantic validation
                               │ utils/            │  ← Response helpers
                               └───────────────────┘
```

### Design Principles

- **Thin controllers**: `function_app.py` handles HTTP concerns only (parse request, call service, return response).
- **Fat services**: All SQL and business logic lives in `services/`. This makes the logic testable without an HTTP layer.
- **No direct DB access**: Clients interact exclusively through Azure Functions HTTP endpoints.
- **Separation of concerns**: Validation (Pydantic), data access (database.py), business logic (services), and transport (function_app.py) are cleanly separated.

---

## 2. Data Model

### Entity-Relationship Diagram

```
┌──────────────────┐         ┌──────────────────────────────────┐
│   Department     │         │           Employee               │
├──────────────────┤         ├──────────────────────────────────┤
│ DepartmentID PK  │◄───────┐│ EmployeeID   PK  IDENTITY(1,1) │
│ DepartmentName   │        ││ FirstName    NOT NULL            │
│ Location (NULL)  │        ││ LastName     NOT NULL            │
└──────────────────┘        ├┤ DepartmentID FK  NOT NULL       │
                            ││ Salary       DECIMAL(12,2)      │
                            ││ Bonus        DECIMAL(12,2) NULL │
                            ││ HireDate     DATE NOT NULL      │
                            │└──────────────────────────────────┘
                            │
                    Many-to-One (N:1)
```

### Key Constraints

| Constraint | Type | Rule |
|-----------|------|------|
| `PK_Employee` | Primary Key | `EmployeeID` (auto-increment) |
| `PK_Department` | Primary Key | `DepartmentID` |
| `FK_Employee_Department` | Foreign Key | `Employee.DepartmentID → Department.DepartmentID` |
| `CK_Employee_Salary_Positive` | Check | `Salary > 0` |
| `CK_Employee_Bonus_NonNegative` | Check | `Bonus IS NULL OR Bonus >= 0` |

### Index Strategy

| Index | Columns | Includes | Purpose |
|-------|---------|----------|---------|
| `IX_Employee_DepartmentID` | `DepartmentID` | `FirstName, LastName, Salary, Bonus` | Covering index for department-filtered employee lists |

### NULL Semantics for Bonus

The `Bonus` column is **nullable by design**. A `NULL` value means:
> *"This employee has not been awarded any bonus."*

This is semantically different from `Bonus = 0` (which would mean "awarded a bonus of zero"). All queries respect this distinction.

---

## 3. API Reference

### Base URL

```
http://localhost:7071/api
```

### Common Response Envelope

**Success (2xx):**
```json
{
    "employeeId": 1,
    "firstName": "Alice",
    ...
}
```

**Error (4xx / 5xx):**
```json
{
    "error": "Human-readable error message"
}
```

---

### Part A — CRUD Endpoints

#### `POST /api/employees`

Create a new employee record.

**Request Body:**
```json
{
    "firstName": "Alice",
    "lastName": "Johnson",
    "departmentId": 1,
    "salary": 130000.00,
    "bonus": 26000.00,
    "hireDate": "2019-03-15"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `firstName` | string | ✅ | Max 50 chars |
| `lastName` | string | ✅ | Max 50 chars |
| `departmentId` | integer | ✅ | Must reference an existing department |
| `salary` | decimal | ✅ | Must be > 0 |
| `bonus` | decimal | ❌ | Omit or set to `null` for no bonus. Must be ≥ 0 if provided. |
| `hireDate` | string (ISO date) | ✅ | Format: `YYYY-MM-DD` |

**Responses:**
| Status | Description |
|--------|-------------|
| `201 Created` | Employee created; returns the new record with ID |
| `400 Bad Request` | Validation failure or missing required fields |
| `409 Conflict` | Integrity constraint violation |

---

#### `GET /api/employees/{id}`

Retrieve a single employee by ID.

**Responses:**
| Status | Description |
|--------|-------------|
| `200 OK` | Returns the employee object |
| `400 Bad Request` | ID is not a valid integer |
| `404 Not Found` | No employee with this ID |

---

#### `GET /api/employees[?departmentId=N]`

List all employees, optionally filtered by department.

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `departmentId` | integer | ❌ | Filter by department ID |

**Response:** Array of employee objects.

---

#### `PUT /api/employees/{id}`

Partial update of an existing employee. Only include the fields you want to change.

**Special field — `clearBonus`:**
To explicitly set the bonus to `NULL` (remove the bonus), send:
```json
{ "clearBonus": true }
```

**Responses:**
| Status | Description |
|--------|-------------|
| `200 OK` | Returns the updated employee |
| `400 Bad Request` | Validation failure |
| `404 Not Found` | Employee not found |

---

#### `DELETE /api/employees/{id}`

Delete an employee by ID.

**Responses:**
| Status | Description |
|--------|-------------|
| `204 No Content` | Successfully deleted |
| `404 Not Found` | Employee not found |

---

### Part B — Reporting Endpoints

#### `GET /api/reports/total-bonus`

**B-1: Total bonus paid company-wide (NULL → 0).**

```json
{
    "totalBonus": 181450.00
}
```

**SQL Logic:** `SUM(COALESCE(Bonus, 0))` — treats NULL as 0 in the aggregation.

---

#### `GET /api/reports/no-bonus`

**B-2: Employees who have never received a bonus.**

```json
[
    {
        "employeeId": 2,
        "firstName": "Bob",
        "lastName": "Smith",
        "departmentId": 1,
        "departmentName": "Engineering",
        "salary": 115000.00,
        "bonus": null,
        "hireDate": "2020-07-01"
    }
]
```

---

#### `GET /api/reports/bonus-percentage`

**B-3: Bonus as a percentage of salary (only employees WITH a bonus).**

```json
[
    {
        "employeeId": 6,
        "firstName": "Fiona",
        "lastName": "Davis",
        "salary": 95000.00,
        "bonus": 28500.00,
        "bonusPercentage": 30.00
    }
]
```

**SQL Logic:** `ROUND(Bonus / Salary * 100, 2)` with `WHERE Bonus IS NOT NULL`.

---

#### `GET /api/reports/departments-high-bonus`

**B-4: Departments where total bonus > department's average salary.**

```json
[
    {
        "departmentId": 3,
        "departmentName": "Sales",
        "totalBonus": 50500.00,
        "avgSalary": 91666.67
    }
]
```

**SQL Logic:** `HAVING SUM(COALESCE(Bonus, 0)) > AVG(Salary)`.

---

#### `GET /api/reports/bonus-ranking`

**B-5: Employees ranked by bonus amount. NULL-bonus employees ranked last.**

```json
[
    { "employeeId": 11, "bonusRank": 1, "bonus": 45000.00 },
    { "employeeId": 3,  "bonusRank": 2, "bonus": 35000.00 },
    { "employeeId": 2,  "bonusRank": 9, "bonus": null }
]
```

**SQL Logic:** Uses `RANK()` with a `CASE` expression to push NULLs to the bottom:
```sql
RANK() OVER (
    ORDER BY
        CASE WHEN Bonus IS NULL THEN 1 ELSE 0 END,
        Bonus DESC
)
```

---

#### `GET /api/reports/highest-salary`

**B-6: Highest base salary employee + highest total compensation comparison.**

```json
{
    "highestSalaryEmployee": {
        "employeeId": 11,
        "firstName": "Kevin",
        "lastName": "Jackson",
        "salary": 150000.00,
        "bonus": 45000.00,
        "totalCompensation": 195000.00
    },
    "highestCompensationEmployee": {
        "employeeId": 11,
        "firstName": "Kevin",
        "lastName": "Jackson",
        "salary": 150000.00,
        "bonus": 45000.00,
        "totalCompensation": 195000.00
    },
    "sameEmployee": true
}
```

---

## 4. SQL Query Design

### NULL Handling Strategy

Every query that involves the `Bonus` column uses explicit NULL handling:

| Pattern | Usage | Where Used |
|---------|-------|------------|
| `COALESCE(Bonus, 0)` | Treat NULL as 0 for aggregation | B-1 (total), B-4 (dept), B-6 (compensation) |
| `WHERE Bonus IS NULL` | Find employees without bonus | B-2 |
| `WHERE Bonus IS NOT NULL` | Find employees with bonus | B-3 |
| `CASE WHEN Bonus IS NULL THEN 1 ELSE 0 END` | Sort NULLs last | B-5 |

### Indexing

The `IX_Employee_DepartmentID` covering index optimises:
- `GET /api/employees?departmentId=N` (direct index seek)
- `GET /api/reports/departments-high-bonus` (group by DepartmentID)

For production scale, consider adding:
- Index on `(Salary DESC)` for B-6
- Index on `(Bonus)` with `WHERE Bonus IS NOT NULL` for B-3

---

## 5. Error Handling Strategy

### Layered Error Handling

```
HTTP Layer (function_app.py)
├── Parse & validate request → 400 Bad Request
├── Call service layer
│   ├── Service returns None → 404 Not Found
│   ├── pyodbc.IntegrityError → 400 / 409
│   └── Unexpected exception → 500 (logged, not exposed)
└── Serialise & return response
```

### HTTP Status Code Usage

| Code | Meaning | When |
|------|---------|------|
| `200` | OK | Successful GET / PUT |
| `201` | Created | Successful POST |
| `204` | No Content | Successful DELETE |
| `400` | Bad Request | Invalid input, missing fields, type errors |
| `404` | Not Found | Resource doesn't exist |
| `409` | Conflict | FK violation, duplicate key |
| `500` | Internal Error | Unhandled exception (details logged server-side) |

### Security Principle

Error responses **never leak** internal details (stack traces, SQL errors) to clients. Detailed error information is written to the Azure Functions log stream only.

---

## 6. Security & Secrets Management

### Local Development

- Connection string is stored in `local.settings.json` (gitignored).
- The file is loaded automatically by the Azure Functions runtime.

### Azure Deployment

- Store `SQL_CONNECTION_STRING` in **Azure App Settings** or **Azure Key Vault**.
- Use **Managed Identity** + Key Vault references for production:
  ```
  @Microsoft.KeyVault(SecretUri=https://your-vault.vault.azure.net/secrets/SqlConnectionString)
  ```

### What is NOT hardcoded

- ✅ Database connection string
- ✅ Database credentials (username/password)
- ✅ Feature flags (`APPLY_DEFAULT_BONUS`)
- ✅ Storage connection string

---

## 7. Default Bonus Feature (Part C)

### Specification

> *"Optional: apply a default bonus equal to 5% of salary to employees who don't have one."*

### Implementation: **Read-Time Calculation**

When `APPLY_DEFAULT_BONUS=true`:
- API responses for employees with `Bonus IS NULL` will show `bonus: <5% of salary>`
- The database value remains `NULL`
- Reporting endpoints (Part B) use raw database values (not the default)

### Why Read-Time Over Write-Time

| Criterion | Read-Time ✅ | Write-Time ❌ |
|-----------|-------------|--------------|
| **Data integrity** | NULL preserved | NULL permanently overwritten |
| **Reversibility** | Toggle env var | Requires data migration |
| **Audit trail** | Can distinguish "no bonus" vs "default" | Cannot distinguish |
| **Performance** | Negligible overhead (simple multiplication) | Requires UPDATE for every insert |
| **Report accuracy** | B-2 ("no bonus" list) still works correctly | B-2 would return empty (all have bonus) |

---

## 8. Testing Guide

### Manual Testing with cURL

```bash
# Create
curl -s -X POST http://localhost:7071/api/employees \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Test","lastName":"User","departmentId":1,"salary":80000,"hireDate":"2024-01-01"}' | python -m json.tool

# Read
curl -s http://localhost:7071/api/employees/1 | python -m json.tool

# List with filter
curl -s "http://localhost:7071/api/employees?departmentId=3" | python -m json.tool

# Update bonus
curl -s -X PUT http://localhost:7071/api/employees/1 \
  -H "Content-Type: application/json" \
  -d '{"bonus": 15000}' | python -m json.tool

# Delete
curl -s -X DELETE http://localhost:7071/api/employees/1 -w "\nHTTP Status: %{http_code}\n"

# Reports
curl -s http://localhost:7071/api/reports/total-bonus | python -m json.tool
curl -s http://localhost:7071/api/reports/no-bonus | python -m json.tool
curl -s http://localhost:7071/api/reports/bonus-percentage | python -m json.tool
curl -s http://localhost:7071/api/reports/departments-high-bonus | python -m json.tool
curl -s http://localhost:7071/api/reports/bonus-ranking | python -m json.tool
curl -s http://localhost:7071/api/reports/highest-salary | python -m json.tool
```

### Edge Cases to Verify

| Test Case | Expected Result |
|-----------|----------------|
| Create employee without bonus | `bonus: null` in response |
| Create employee with invalid `departmentId` | `400` with FK error message |
| GET non-existent employee | `404` |
| PUT with `{ "clearBonus": true }` | Bonus set to NULL |
| DELETE then GET same ID | `404` |
| Report: all bonuses NULL | Total bonus = 0, no-bonus list = all employees |
| Report: single employee | Rankings still work correctly |

---

## 9. Deployment to Azure

### Step-by-Step

```bash
# 1. Login to Azure
az login

# 2. Create resource group
az group create --name rg-compensation --location eastus

# 3. Create storage account (required by Functions)
az storage account create \
  --name stcompensation \
  --resource-group rg-compensation \
  --sku Standard_LRS

# 4. Create Function App
az functionapp create \
  --resource-group rg-compensation \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name func-compensation \
  --storage-account stcompensation \
  --os-type Linux

# 5. Set connection string (use Key Vault in production!)
az functionapp config appsettings set \
  --resource-group rg-compensation \
  --name func-compensation \
  --settings "SQL_CONNECTION_STRING=<your-connection-string>"

# 6. Deploy
func azure functionapp publish func-compensation
```

---

## 10. Known Assumptions

| # | Assumption | Rationale |
|---|-----------|-----------|
| 1 | `DepartmentID` in the Department table is **manually assigned** (not IDENTITY) | Assignment specifies PK but not auto-increment; departments are typically created by admins |
| 2 | `HireDate` is required on creation | Every employee has a hire date; the column has no DEFAULT |
| 3 | Partial updates via PUT (not PATCH) | PUT is used for partial updates for simplicity; a strict REST API would use PATCH |
| 4 | `Bonus = NULL` and `Bonus = 0` are semantically different | NULL = "not awarded", 0 = "awarded zero bonus" |
| 5 | The optional default bonus (5%) applies only to CRUD read responses, not to reporting endpoints | Reports should reflect actual data for accuracy |
| 6 | Authentication is set to `ANONYMOUS` for local development | Production should use Function keys or Azure AD |
| 7 | The service uses connection-per-request with ODBC pooling | pyodbc leverages ODBC driver's built-in connection pooling |
