-- ============================================================
-- Script: 02_create_tables.sql
-- Purpose: Create Department and Employee tables with
--          constraints, indexes, and referential integrity.
-- Run against the [EmployeeCompensation] database.
-- ============================================================

USE EmployeeCompensation;
GO

-- ---------- Department ----------
IF OBJECT_ID('dbo.Employee', 'U') IS NOT NULL
    DROP TABLE dbo.Employee;
IF OBJECT_ID('dbo.Department', 'U') IS NOT NULL
    DROP TABLE dbo.Department;
GO

CREATE TABLE dbo.Department (
    DepartmentID   INT            NOT NULL  PRIMARY KEY,
    DepartmentName VARCHAR(100)   NOT NULL,
    Location       VARCHAR(100)   NULL
);
GO

-- ---------- Employee ----------
CREATE TABLE dbo.Employee (
    EmployeeID   INT            NOT NULL  IDENTITY(1,1)  PRIMARY KEY,
    FirstName    VARCHAR(50)    NOT NULL,
    LastName     VARCHAR(50)    NOT NULL,
    DepartmentID INT            NOT NULL,
    Salary       DECIMAL(12,2)  NOT NULL,
    Bonus        DECIMAL(12,2)  NULL,       -- NULL = no bonus awarded
    HireDate     DATE           NOT NULL,

    CONSTRAINT FK_Employee_Department
        FOREIGN KEY (DepartmentID)
        REFERENCES dbo.Department (DepartmentID)
        ON DELETE NO ACTION
        ON UPDATE CASCADE,

    CONSTRAINT CK_Employee_Salary_Positive
        CHECK (Salary > 0),

    CONSTRAINT CK_Employee_Bonus_NonNegative
        CHECK (Bonus IS NULL OR Bonus >= 0)
);
GO

-- Index for the most common filter (list employees by department)
CREATE NONCLUSTERED INDEX IX_Employee_DepartmentID
    ON dbo.Employee (DepartmentID)
    INCLUDE (FirstName, LastName, Salary, Bonus);
GO

PRINT 'Tables created successfully.';
GO
