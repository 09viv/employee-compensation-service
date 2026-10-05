-- ============================================================
-- Script: 01_create_database.sql
-- Purpose: Create the EmployeeCompensation database
-- Run this FIRST, against the 'master' database.
-- ============================================================

IF DB_ID('EmployeeCompensation') IS NULL
BEGIN
    CREATE DATABASE EmployeeCompensation;
    PRINT 'Database [EmployeeCompensation] created successfully.';
END
ELSE
BEGIN
    PRINT 'Database [EmployeeCompensation] already exists — skipping.';
END
GO
