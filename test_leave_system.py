"""
Automated Unit Test Suite for Employee Leave Management System (Project No. 72)
Verifies all 4 official project test cases and additional edge cases.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from employee_leave_system import (
    apply_leave,
    calculate_leave_days,
    check_leave_balance,
    get_balance_string,
    get_initial_employee_database,
    parse_and_validate_dates,
    validate_employee_id,
    validate_leave_type,
)


class TestEmployeeLeaveManagementSystem(unittest.TestCase):
    def setUp(self) -> None:
        """Create a fresh isolated copy of the database before each test."""
        self.db = get_initial_employee_database()

    # --------------------------------------------------------------------------
    # Official Project Specification Test Cases (1 to 4)
    # --------------------------------------------------------------------------

    def test_case_1_normal_input(self) -> None:
        """
        Test Case 1: Normal Input
        Input:
            ID: E101, Type: Casual, From: 2026-12-10, To: 2026-12-12
        Expected Output:
            Leave approved: 3 days Casual | Balance Casual: 9
        """
        success, message = apply_leave("E101", "Casual", "2026-12-10", "2026-12-12", self.db)
        self.assertTrue(success)
        self.assertEqual(message, "Leave approved: 3 days Casual | Balance Casual: 9")
        self.assertEqual(self.db["E101"]["balances"]["Casual"], 9)

    def test_case_2_boundary_minimum_input(self) -> None:
        """
        Test Case 2: Boundary / Minimum Input
        Input:
            ID: E101, Type: Casual, From: 2026-11-02, To: 2026-11-13 (12 days = full balance)
        Expected Output:
            Leave approved: 12 days Casual | Balance Casual: 0
        """
        success, message = apply_leave("E101", "Casual", "2026-11-02", "2026-11-13", self.db)
        self.assertTrue(success)
        self.assertEqual(message, "Leave approved: 12 days Casual | Balance Casual: 0")
        self.assertEqual(self.db["E101"]["balances"]["Casual"], 0)

    def test_case_3_invalid_input_to_before_from(self) -> None:
        """
        Test Case 3: Invalid Input
        Input:
            ID: E101, Type: Sick, From: 2026-12-15, To: 2026-12-10
        Expected Output:
            Invalid dates. To-date cannot be before from-date.
        """
        success, message = apply_leave("E101", "Sick", "2026-12-15", "2026-12-10", self.db)
        self.assertFalse(success)
        self.assertEqual(message, "Invalid dates. To-date cannot be before from-date.")
        # Ensure Sick balance remains completely untouched (10 days)
        self.assertEqual(self.db["E101"]["balances"]["Sick"], 10)

    def test_case_4_different_valid_scenario_and_view_balance(self) -> None:
        """
        Test Case 4: Different Valid Scenario
        Input:
            (a) Apply: ID: E101, Casual, From: 2027-01-01, To: 2027-01-14 (14 days requested > 12)
            (b) View balance: ID: E101
        Expected Output:
            (a) Leave rejected. Requested: 14 days | Available: 12 days
            (b) Casual: 12 | Sick: 10 | Earned: 15
        """
        # Step (a): Apply for 14 days
        success, message = apply_leave("E101", "Casual", "2027-01-01", "2027-01-14", self.db)
        self.assertFalse(success)
        self.assertEqual(message, "Leave rejected. Requested: 14 days | Available: 12 days")

        # Step (b): View balance for E101
        bal_success, bal_string = get_balance_string("E101", self.db)
        self.assertTrue(bal_success)
        self.assertEqual(bal_string, "Casual: 12 | Sick: 10 | Earned: 15")

    # --------------------------------------------------------------------------
    # Additional Verification & Boundary Tests
    # --------------------------------------------------------------------------

    def test_single_day_inclusive_leave(self) -> None:
        """Ensure single-day leave (from == to) calculates as exactly 1 day."""
        days = calculate_leave_days(date(2026, 12, 10), date(2026, 12, 10))
        self.assertEqual(days, 1)

        success, message = apply_leave("E101", "Sick", "2026-12-10", "2026-12-10", self.db)
        self.assertTrue(success)
        self.assertEqual(message, "Leave approved: 1 days Sick | Balance Sick: 9")

    def test_case_insensitive_inputs(self) -> None:
        """Check that lowercase 'e101' and 'casual' are handled seamlessly."""
        success, message = apply_leave("e101", "casual", "2026-12-10", "2026-12-11", self.db)
        self.assertTrue(success)
        self.assertEqual(message, "Leave approved: 2 days Casual | Balance Casual: 10")

    def test_invalid_employee_id(self) -> None:
        """Validate non-existent employee ID error handling."""
        valid, _, err = validate_employee_id("E999", self.db)
        self.assertFalse(valid)
        self.assertIn("not found in records", err)

        success, message = apply_leave("E999", "Casual", "2026-12-10", "2026-12-12", self.db)
        self.assertFalse(success)
        self.assertIn("not found in records", message)

    def test_invalid_leave_type(self) -> None:
        """Validate unauthorized leave type error handling."""
        valid, _, err = validate_leave_type("Maternity")
        self.assertFalse(valid)
        self.assertIn("Invalid leave type", err)

        success, message = apply_leave("E101", "Maternity", "2026-12-10", "2026-12-12", self.db)
        self.assertFalse(success)
        self.assertIn("Invalid leave type", message)

    def test_invalid_date_format(self) -> None:
        """Validate malformed date string error handling."""
        valid, _, _, _, err = parse_and_validate_dates("10-12-2026", "2026-12-12")
        self.assertFalse(valid)
        self.assertIn("Invalid date format", err)

        success, message = apply_leave("E101", "Casual", "10-12-2026", "2026-12-12", self.db)
        self.assertFalse(success)
        self.assertIn("Invalid date format", message)


if __name__ == "__main__":
    unittest.main()
