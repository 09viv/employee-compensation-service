-- ============================================================
-- Script: 03_seed_data.sql
-- Purpose: Insert sample departments and employees.
--          Includes a mix of employees WITH and WITHOUT bonuses
--          to exercise every reporting query.
-- Run against the [EmployeeCompensation] database.
-- ============================================================

USE EmployeeCompensation;
GO

-- ---------- Departments ----------
INSERT INTO dbo.Department (DepartmentID, DepartmentName, Location) VALUES
(1,  'Engineering',       'San Francisco'),
(2,  'Human Resources',   'New York'),
(3,  'Sales',             'Chicago'),
(4,  'Marketing',         'Austin'),
(5,  'Finance',           NULL);              -- Location intentionally NULL
GO

-- ---------- Employees ----------
-- Mix of bonuses: some generous, some modest, some NULL.
INSERT INTO dbo.Employee (FirstName, LastName, DepartmentID, Salary, Bonus, HireDate) VALUES
-- Engineering (Dept 1)
('Alice',   'Johnson',   1,  130000.00,  26000.00,  '2019-03-15'),
('Bob',     'Smith',     1,  115000.00,  NULL,       '2020-07-01'),
('Charlie', 'Lee',       1,  140000.00,  35000.00,  '2018-01-10'),

-- Human Resources (Dept 2)
('Diana',   'Martinez',  2,   85000.00,   4250.00,  '2021-06-20'),
('Ethan',   'Brown',     2,   78000.00,  NULL,       '2022-09-05'),

-- Sales (Dept 3)
('Fiona',   'Davis',     3,   95000.00,  28500.00,  '2017-11-30'),
('George',  'Wilson',    3,   88000.00,  22000.00,  '2019-04-22'),
('Hannah',  'Taylor',    3,   92000.00,  NULL,       '2023-01-15'),

-- Marketing (Dept 4)
('Ian',     'Anderson',  4,   82000.00,   8200.00,  '2020-10-01'),
('Julia',   'Thomas',    4,   79000.00,  NULL,       '2024-03-12'),

-- Finance (Dept 5)
('Kevin',   'Jackson',   5,  150000.00,  45000.00,  '2016-05-18'),
('Laura',   'White',     5,  125000.00,  12500.00,  '2019-08-25');
GO

PRINT 'Seed data inserted successfully.';
GO
