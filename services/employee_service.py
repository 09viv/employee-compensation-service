"""
Employee CRUD service.

All data access is encapsulated here — the Azure Functions layer
never touches SQL directly.
"""

import os
import logging
from decimal import Decimal
from typing import Any

from services.database import execute_query, execute_command, execute_scalar

logger = logging.getLogger(__name__)

# ---------- helpers ----------

def _apply_default_bonus_flag() -> bool:
    """Check if the optional 5 % default-bonus feature is enabled."""
    return os.environ.get("APPLY_DEFAULT_BONUS", "false").lower() == "true"


def _row_to_dict(row: dict) -> dict:
    """
    Map a DB row to the API response shape (camelCase keys).

    If APPLY_DEFAULT_BONUS is enabled AND Bonus is NULL, the response
    will show a calculated default of 5 % of Salary.  The underlying
    data is NOT mutated — this is a read-time calculation so we
    preserve the original NULL semantics in the database.
    """
    bonus = row.get("Bonus")
    salary = row.get("Salary")

    if bonus is None and _apply_default_bonus_flag() and salary is not None:
        bonus = round(Decimal(str(salary)) * Decimal("0.05"), 2)

    return {
        "employeeId": row["EmployeeID"],
        "firstName": row["FirstName"],
        "lastName": row["LastName"],
        "departmentId": row["DepartmentID"],
        "salary": salary,
        "bonus": bonus,
        "hireDate": row["HireDate"],
        "departmentName": row.get("DepartmentName"),
    }


# ---------- CRUD ----------

def create_employee(data: dict[str, Any]) -> dict:
    """Insert a new employee and return the created record."""
    query = """
        INSERT INTO dbo.Employee
            (FirstName, LastName, DepartmentID, Salary, Bonus, HireDate)
        OUTPUT INSERTED.EmployeeID
        VALUES (?, ?, ?, ?, ?, ?);
    """
    params = (
        data["firstName"],
        data["lastName"],
        data["departmentId"],
        data["salary"],
        data.get("bonus"),  # may be None
        data["hireDate"],
    )
    new_id = execute_scalar(query, params)
    return get_employee_by_id(int(new_id))


def get_employee_by_id(employee_id: int) -> dict | None:
    """Return a single employee with their department name, or None."""
    query = """
        SELECT e.EmployeeID, e.FirstName, e.LastName, e.DepartmentID,
               e.Salary, e.Bonus, e.HireDate,
               d.DepartmentName
        FROM   dbo.Employee   e
        JOIN   dbo.Department d ON e.DepartmentID = d.DepartmentID
        WHERE  e.EmployeeID = ?
    """
    row = execute_query(query, (employee_id,), fetch_one=True)
    return _row_to_dict(row) if row else None


def list_employees(department_id: int | None = None) -> list[dict]:
    """Return all employees, optionally filtered by department."""
    query = """
        SELECT e.EmployeeID, e.FirstName, e.LastName, e.DepartmentID,
               e.Salary, e.Bonus, e.HireDate,
               d.DepartmentName
        FROM   dbo.Employee   e
        JOIN   dbo.Department d ON e.DepartmentID = d.DepartmentID
    """
    params: tuple = ()
    if department_id is not None:
        query += " WHERE e.DepartmentID = ?"
        params = (department_id,)

    query += " ORDER BY e.EmployeeID"
    rows = execute_query(query, params)
    return [_row_to_dict(r) for r in rows]


def update_employee(employee_id: int, data: dict[str, Any]) -> dict | None:
    """
    Partially update an employee.

    Only the fields present in `data` are updated.  To explicitly
    clear the bonus (set to NULL), send { "clearBonus": true }.
    """
    set_clauses: list[str] = []
    params: list = []

    field_map = {
        "firstName": "FirstName",
        "lastName": "LastName",
        "departmentId": "DepartmentID",
        "salary": "Salary",
        "bonus": "Bonus",
        "hireDate": "HireDate",
    }

    for api_key, col in field_map.items():
        if api_key in data and data[api_key] is not None:
            set_clauses.append(f"{col} = ?")
            params.append(data[api_key])

    # Handle explicit bonus clearing
    if data.get("clearBonus"):
        set_clauses.append("Bonus = NULL")

    if not set_clauses:
        # Nothing to update — just return current state
        return get_employee_by_id(employee_id)

    params.append(employee_id)
    query = f"""
        UPDATE dbo.Employee
        SET    {', '.join(set_clauses)}
        WHERE  EmployeeID = ?
    """
    affected = execute_command(query, tuple(params))
    if affected == 0:
        return None
    return get_employee_by_id(employee_id)


def delete_employee(employee_id: int) -> bool:
    """Delete an employee. Returns True if a row was deleted."""
    query = "DELETE FROM dbo.Employee WHERE EmployeeID = ?"
    affected = execute_command(query, (employee_id,))
    return affected > 0
