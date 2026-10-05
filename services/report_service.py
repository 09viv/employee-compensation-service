"""
Compensation reporting service.

Implements the six reporting queries from Part B of the assignment.
Every query handles NULL bonuses explicitly as required.
"""

import logging

from services.database import execute_query

logger = logging.getLogger(__name__)


def get_total_bonus() -> dict:
    """
    B-1: Total bonus paid across the entire company.
    Employees without a bonus are treated as 0.
    """
    query = """
        SELECT COALESCE(SUM(COALESCE(Bonus, 0)), 0) AS TotalBonus
        FROM   dbo.Employee
    """
    row = execute_query(query, fetch_one=True)
    return {"totalBonus": row["TotalBonus"]}


def get_employees_without_bonus() -> list[dict]:
    """
    B-2: All employees who have never received a bonus (Bonus IS NULL).
    """
    query = """
        SELECT e.EmployeeID, e.FirstName, e.LastName, e.DepartmentID,
               e.Salary, e.Bonus, e.HireDate,
               d.DepartmentName
        FROM   dbo.Employee   e
        JOIN   dbo.Department d ON e.DepartmentID = d.DepartmentID
        WHERE  e.Bonus IS NULL
        ORDER  BY e.EmployeeID
    """
    rows = execute_query(query)
    return [
        {
            "employeeId": r["EmployeeID"],
            "firstName": r["FirstName"],
            "lastName": r["LastName"],
            "departmentId": r["DepartmentID"],
            "departmentName": r["DepartmentName"],
            "salary": r["Salary"],
            "bonus": None,
            "hireDate": r["HireDate"],
        }
        for r in rows
    ]


def get_bonus_percentages() -> list[dict]:
    """
    B-3: For each employee who HAS a bonus, their bonus as a percentage
    of salary, rounded to 2 decimal places.
    """
    query = """
        SELECT e.EmployeeID, e.FirstName, e.LastName,
               e.Salary, e.Bonus,
               ROUND(e.Bonus / e.Salary * 100, 2) AS BonusPercentage
        FROM   dbo.Employee e
        WHERE  e.Bonus IS NOT NULL
        ORDER  BY BonusPercentage DESC
    """
    rows = execute_query(query)
    return [
        {
            "employeeId": r["EmployeeID"],
            "firstName": r["FirstName"],
            "lastName": r["LastName"],
            "salary": r["Salary"],
            "bonus": r["Bonus"],
            "bonusPercentage": r["BonusPercentage"],
        }
        for r in rows
    ]


def get_departments_bonus_exceeds_avg_salary() -> list[dict]:
    """
    B-4: Departments where the total bonus paid exceeds the
    department's average salary.
    """
    query = """
        SELECT d.DepartmentID,
               d.DepartmentName,
               SUM(COALESCE(e.Bonus, 0))  AS TotalBonus,
               AVG(e.Salary)              AS AvgSalary
        FROM   dbo.Department d
        JOIN   dbo.Employee   e ON d.DepartmentID = e.DepartmentID
        GROUP  BY d.DepartmentID, d.DepartmentName
        HAVING SUM(COALESCE(e.Bonus, 0)) > AVG(e.Salary)
        ORDER  BY TotalBonus DESC
    """
    rows = execute_query(query)
    return [
        {
            "departmentId": r["DepartmentID"],
            "departmentName": r["DepartmentName"],
            "totalBonus": r["TotalBonus"],
            "avgSalary": r["AvgSalary"],
        }
        for r in rows
    ]


def get_employees_ranked_by_bonus() -> list[dict]:
    """
    B-5: All employees ranked by bonus amount.
    Employees without a bonus are ranked LAST, not excluded.
    """
    query = """
        SELECT e.EmployeeID, e.FirstName, e.LastName,
               e.Salary, e.Bonus,
               RANK() OVER (
                   ORDER BY
                       CASE WHEN e.Bonus IS NULL THEN 1 ELSE 0 END,
                       e.Bonus DESC
               ) AS BonusRank
        FROM   dbo.Employee e
    """
    rows = execute_query(query)
    return [
        {
            "employeeId": r["EmployeeID"],
            "firstName": r["FirstName"],
            "lastName": r["LastName"],
            "salary": r["Salary"],
            "bonus": r["Bonus"],
            "bonusRank": r["BonusRank"],
        }
        for r in rows
    ]


def get_highest_salary_analysis() -> dict:
    """
    B-6: The employee with the highest base salary, and — separately —
    whether that same person also has the highest total compensation
    (salary + bonus).
    """
    # Highest base salary
    highest_salary_query = """
        SELECT TOP 1
               EmployeeID, FirstName, LastName,
               Salary, Bonus,
               (Salary + COALESCE(Bonus, 0)) AS TotalCompensation
        FROM   dbo.Employee
        ORDER  BY Salary DESC
    """
    # Highest total compensation
    highest_comp_query = """
        SELECT TOP 1
               EmployeeID, FirstName, LastName,
               Salary, Bonus,
               (Salary + COALESCE(Bonus, 0)) AS TotalCompensation
        FROM   dbo.Employee
        ORDER  BY (Salary + COALESCE(Bonus, 0)) DESC
    """
    top_salary = execute_query(highest_salary_query, fetch_one=True)
    top_comp = execute_query(highest_comp_query, fetch_one=True)

    same_person = (
        top_salary["EmployeeID"] == top_comp["EmployeeID"]
        if top_salary and top_comp
        else False
    )

    def _fmt(row: dict | None) -> dict | None:
        if row is None:
            return None
        return {
            "employeeId": row["EmployeeID"],
            "firstName": row["FirstName"],
            "lastName": row["LastName"],
            "salary": row["Salary"],
            "bonus": row["Bonus"],
            "totalCompensation": row["TotalCompensation"],
        }

    return {
        "highestSalaryEmployee": _fmt(top_salary),
        "highestCompensationEmployee": _fmt(top_comp),
        "sameEmployee": same_person,
    }
