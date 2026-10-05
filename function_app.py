"""
Employee Compensation Service — Azure Functions entry point.

Python v2 programming model.  All HTTP-triggered functions are
registered here via the @app decorator.
"""

import json
import logging

import azure.functions as func
import pyodbc
from pydantic import ValidationError

from services import employee_service, report_service
from utils.responses import (
    ok, created, no_content,
    bad_request, not_found, conflict, internal_error,
)

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)
logger = logging.getLogger(__name__)


# ===================================================================
#  Part A — Employee CRUD
# ===================================================================

@app.route(route="employees", methods=["POST"])
def create_employee(req: func.HttpRequest) -> func.HttpResponse:
    """Create a new employee.  Bonus is optional and may be omitted."""
    try:
        body = req.get_json()
    except ValueError:
        return bad_request("Request body must be valid JSON.")

    # Validate with Pydantic
    from models.schemas import EmployeeCreate
    try:
        model = EmployeeCreate.model_validate(body)
    except ValidationError as exc:
        return bad_request(exc.errors()[0]["msg"])

    try:
        data = model.model_dump(by_alias=True)
        # Convert date to string for pyodbc
        data["hireDate"] = str(data["hireDate"])
        result = employee_service.create_employee(data)
        return created(result)
    except pyodbc.IntegrityError as exc:
        if "FOREIGN KEY" in str(exc):
            return bad_request(
                f"Department with ID {body.get('departmentId')} does not exist."
            )
        return conflict(str(exc))
    except Exception as exc:
        logger.exception("Failed to create employee")
        return internal_error()


@app.route(route="employees/{employee_id}", methods=["GET"])
def get_employee(req: func.HttpRequest) -> func.HttpResponse:
    """Retrieve a single employee by their ID."""
    try:
        employee_id = int(req.route_params["employee_id"])
    except (KeyError, ValueError):
        return bad_request("employee_id must be a positive integer.")

    try:
        result = employee_service.get_employee_by_id(employee_id)
        if result is None:
            return not_found(f"Employee with ID {employee_id} not found.")
        return ok(result)
    except Exception as exc:
        logger.exception("Failed to retrieve employee %s", employee_id)
        return internal_error()


@app.route(route="employees", methods=["GET"])
def list_employees(req: func.HttpRequest) -> func.HttpResponse:
    """
    List all employees.
    Optional query parameter: departmentId (int) to filter by department.
    """
    department_id = req.params.get("departmentId")
    if department_id is not None:
        try:
            department_id = int(department_id)
        except ValueError:
            return bad_request("departmentId must be an integer.")

    try:
        results = employee_service.list_employees(department_id)
        return ok(results)
    except Exception as exc:
        logger.exception("Failed to list employees")
        return internal_error()


@app.route(route="employees/{employee_id}", methods=["PUT"])
def update_employee(req: func.HttpRequest) -> func.HttpResponse:
    """Update an existing employee (partial update)."""
    try:
        employee_id = int(req.route_params["employee_id"])
    except (KeyError, ValueError):
        return bad_request("employee_id must be a positive integer.")

    try:
        body = req.get_json()
    except ValueError:
        return bad_request("Request body must be valid JSON.")

    from models.schemas import EmployeeUpdate
    try:
        model = EmployeeUpdate.model_validate(body)
    except ValidationError as exc:
        return bad_request(exc.errors()[0]["msg"])

    try:
        # Build dict of only non-None fields (partial update)
        data = model.model_dump(by_alias=True, exclude_none=True)
        # Always pass clearBonus through
        data["clearBonus"] = model.clear_bonus
        if "hireDate" in data:
            data["hireDate"] = str(data["hireDate"])

        result = employee_service.update_employee(employee_id, data)
        if result is None:
            return not_found(f"Employee with ID {employee_id} not found.")
        return ok(result)
    except pyodbc.IntegrityError as exc:
        if "FOREIGN KEY" in str(exc):
            return bad_request(
                f"Department with ID {body.get('departmentId')} does not exist."
            )
        return conflict(str(exc))
    except Exception as exc:
        logger.exception("Failed to update employee %s", employee_id)
        return internal_error()


@app.route(route="employees/{employee_id}", methods=["DELETE"])
def delete_employee(req: func.HttpRequest) -> func.HttpResponse:
    """Delete an employee by ID."""
    try:
        employee_id = int(req.route_params["employee_id"])
    except (KeyError, ValueError):
        return bad_request("employee_id must be a positive integer.")

    try:
        deleted = employee_service.delete_employee(employee_id)
        if not deleted:
            return not_found(f"Employee with ID {employee_id} not found.")
        return no_content()
    except Exception as exc:
        logger.exception("Failed to delete employee %s", employee_id)
        return internal_error()


# ===================================================================
#  Part B — Compensation Reporting
# ===================================================================

@app.route(route="reports/total-bonus", methods=["GET"])
def report_total_bonus(req: func.HttpRequest) -> func.HttpResponse:
    """B-1: Total bonus paid across the whole company (NULL → 0)."""
    try:
        return ok(report_service.get_total_bonus())
    except Exception as exc:
        logger.exception("Report failed: total-bonus")
        return internal_error()


@app.route(route="reports/no-bonus", methods=["GET"])
def report_no_bonus(req: func.HttpRequest) -> func.HttpResponse:
    """B-2: Employees who have never received a bonus."""
    try:
        return ok(report_service.get_employees_without_bonus())
    except Exception as exc:
        logger.exception("Report failed: no-bonus")
        return internal_error()


@app.route(route="reports/bonus-percentage", methods=["GET"])
def report_bonus_percentage(req: func.HttpRequest) -> func.HttpResponse:
    """B-3: Bonus as a % of salary for employees who have a bonus."""
    try:
        return ok(report_service.get_bonus_percentages())
    except Exception as exc:
        logger.exception("Report failed: bonus-percentage")
        return internal_error()


@app.route(route="reports/departments-high-bonus", methods=["GET"])
def report_departments_high_bonus(req: func.HttpRequest) -> func.HttpResponse:
    """B-4: Departments where total bonus > average salary."""
    try:
        return ok(report_service.get_departments_bonus_exceeds_avg_salary())
    except Exception as exc:
        logger.exception("Report failed: departments-high-bonus")
        return internal_error()


@app.route(route="reports/bonus-ranking", methods=["GET"])
def report_bonus_ranking(req: func.HttpRequest) -> func.HttpResponse:
    """B-5: Employees ranked by bonus (NULL-bonus employees ranked last)."""
    try:
        return ok(report_service.get_employees_ranked_by_bonus())
    except Exception as exc:
        logger.exception("Report failed: bonus-ranking")
        return internal_error()


@app.route(route="reports/highest-salary", methods=["GET"])
def report_highest_salary(req: func.HttpRequest) -> func.HttpResponse:
    """B-6: Highest salary employee and whether they also have highest total comp."""
    try:
        return ok(report_service.get_highest_salary_analysis())
    except Exception as exc:
        logger.exception("Report failed: highest-salary")
        return internal_error()
