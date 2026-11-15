"""
Employee Leave Management System
================================
Institution : Rungta International Skills University
School      : School of Computer Science and Engineering
Program     : Bachelor of Technology - Computer Science and Engineering
Course      : Programming Fundamentals and Logic Building Using Python (RU-100-01-0021)
PS No.      : 72
Project     : Employee Leave Management System
Language    : Python 3
Concepts    : Dictionaries, Conditions, Functions, Dates, CSV Data Persistence
"""

from __future__ import annotations

import copy
import csv
import os
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

# Terminal encoding stabilization for Windows PowerShell and Unix shells
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ==============================================================================
# Domain Constants & Configuration
# ==============================================================================

DEFAULT_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employees.csv")
AUDIT_LOG_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leave_records.csv")

VALID_LEAVE_TYPES = ("Casual", "Sick", "Earned")

# Default benchmark seed dictionary (Requirement 2 & fallback)
DEFAULT_EMPLOYEES: Dict[str, Dict[str, Any]] = {
    "E101": {
        "name": "Amit",
        "department": "Software Engineering",
        "balances": {
            "Casual": 12,
            "Sick": 10,
            "Earned": 15,
        },
    },
    "E102": {
        "name": "Priya Sharma",
        "department": "Quality Assurance",
        "balances": {
            "Casual": 10,
            "Sick": 8,
            "Earned": 12,
        },
    },
    "E103": {
        "name": "Rahul Verma",
        "department": "Product Management",
        "balances": {
            "Casual": 12,
            "Sick": 10,
            "Earned": 20,
        },
    },
}


def get_initial_employee_database() -> Dict[str, Dict[str, Any]]:
    """Returns an isolated deep copy of the default employee database."""
    return copy.deepcopy(DEFAULT_EMPLOYEES)


# ==============================================================================
# Data Persistence Layer (CSV <-> In-Memory Nested Dictionary)
# ==============================================================================

def load_employees_from_csv(file_path: str = DEFAULT_CSV_PATH) -> Dict[str, Dict[str, Any]]:
    """
    Loads employee records from CSV file into the required nested dictionary structure.
    If the file is missing or empty, gracefully bootstraps from DEFAULT_EMPLOYEES.

    Nested Dictionary Schema:
        {
            "E101": {
                "name": str,
                "department": str,
                "balances": {
                    "Casual": int,
                    "Sick": int,
                    "Earned": int
                }
            }
        }
    """
    if not os.path.exists(file_path):
        # Bootstrap default CSV if missing
        save_employees_to_csv(DEFAULT_EMPLOYEES, file_path)
        return copy.deepcopy(DEFAULT_EMPLOYEES)

    database: Dict[str, Dict[str, Any]] = {}
    try:
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned_row = {k.strip(): v.strip() for k, v in row.items() if k}
                emp_id = cleaned_row.get("EmployeeID", "").upper()
                if not emp_id:
                    continue

                database[emp_id] = {
                    "name": cleaned_row.get("Name", "Unknown"),
                    "department": cleaned_row.get("Department", "General"),
                    "balances": {
                        "Casual": int(cleaned_row.get("Casual", 0)),
                        "Sick": int(cleaned_row.get("Sick", 0)),
                        "Earned": int(cleaned_row.get("Earned", 0)),
                    },
                }

        if not database:
            return copy.deepcopy(DEFAULT_EMPLOYEES)
        return database

    except Exception:
        # Fallback to in-memory default state on any I/O error
        return copy.deepcopy(DEFAULT_EMPLOYEES)


def save_employees_to_csv(
    db: Dict[str, Dict[str, Any]],
    file_path: str = DEFAULT_CSV_PATH
) -> bool:
    """Persists active nested dictionary state to CSV."""
    try:
        fieldnames = ["EmployeeID", "Name", "Department", "Casual", "Sick", "Earned"]
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for emp_id, data in db.items():
                b = data["balances"]
                writer.writerow({
                    "EmployeeID": emp_id,
                    "Name": data["name"],
                    "Department": data["department"],
                    "Casual": b.get("Casual", 0),
                    "Sick": b.get("Sick", 0),
                    "Earned": b.get("Earned", 0),
                })
        return True
    except Exception:
        return False


def log_leave_audit(
    emp_id: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    days: int,
    status: str,
    remaining_balance: int,
    log_path: str = AUDIT_LOG_CSV_PATH
) -> None:
    """Appends an immutable audit transaction to leave_records.csv."""
    try:
        file_exists = os.path.exists(log_path)
        with open(log_path, mode="a", newline="", encoding="utf-8") as f:
            fieldnames = [
                "RecordID", "EmployeeID", "LeaveType", "FromDate",
                "ToDate", "Days", "Status", "RemainingBalance", "Timestamp"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()

            rec_id = f"REC{int(datetime.now().timestamp()) % 100000:05d}"
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow({
                "RecordID": rec_id,
                "EmployeeID": emp_id,
                "LeaveType": leave_type,
                "FromDate": from_date,
                "ToDate": to_date,
                "Days": days,
                "Status": status,
                "RemainingBalance": remaining_balance,
                "Timestamp": now_str,
            })
    except Exception:
        pass


# Active runtime database instance
employee_database: Dict[str, Dict[str, Any]] = load_employees_from_csv()


# ==============================================================================
# Validation & Parsing Layer (Requirements 3 & 4)
# ==============================================================================

def validate_employee_id(
    emp_id: str,
    db: Optional[Dict[str, Dict[str, Any]]] = None
) -> Tuple[bool, str, str]:
    """
    Validates employee identification code against active database.
    Case-insensitive normalization: 'e101' -> 'E101'.
    """
    if db is None:
        db = employee_database

    cleaned = (emp_id or "").strip().upper()
    if not cleaned:
        return False, "", "Employee ID cannot be empty."

    if cleaned not in db:
        return False, cleaned, f"Employee ID '{cleaned}' not found in records."

    return True, cleaned, ""


def validate_leave_type(leave_type_input: str) -> Tuple[bool, str, str]:
    """
    Validates and normalizes leave type (Casual, Sick, Earned).
    Case-insensitive matching.
    """
    cleaned = (leave_type_input or "").strip().lower()
    for valid in VALID_LEAVE_TYPES:
        if cleaned == valid.lower():
            return True, valid, ""

    allowed_types_str = ", ".join(VALID_LEAVE_TYPES)
    return False, "", f"Invalid leave type. Allowed types: {allowed_types_str}"


def parse_and_validate_dates(
    from_date_str: str,
    to_date_str: str
) -> Tuple[bool, Optional[date], Optional[date], int, str]:
    """
    Parses dates in YYYY-MM-DD format using datetime module and computes inclusive duration.

    Invariant Rules:
      1. Format must adhere to YYYY-MM-DD.
      2. To-date cannot be chronologically prior to From-date.
      3. Leave duration is inclusive: (to_date - from_date).days + 1.
    """
    from_clean = (from_date_str or "").strip()
    to_clean = (to_date_str or "").strip()

    try:
        from_dt = datetime.strptime(from_clean, "%Y-%m-%d").date()
    except ValueError:
        return False, None, None, 0, f"Invalid date format for From-date ('{from_clean}'). Please use YYYY-MM-DD."

    try:
        to_dt = datetime.strptime(to_clean, "%Y-%m-%d").date()
    except ValueError:
        return False, None, None, 0, f"Invalid date format for To-date ('{to_clean}'). Please use YYYY-MM-DD."

    # Test Case 3 Specification Output
    if to_dt < from_dt:
        return False, from_dt, to_dt, 0, "Invalid dates. To-date cannot be before from-date."

    days = calculate_leave_days(from_dt, to_dt)
    return True, from_dt, to_dt, days, ""


def calculate_leave_days(from_date_obj: date, to_date_obj: date) -> int:
    """Calculates number of leave days inclusive of both dates: (to - from) + 1."""
    return (to_date_obj - from_date_obj).days + 1


# ==============================================================================
# Domain Core Logic (Requirements 4 & 5)
# ==============================================================================

def check_leave_balance(
    emp_id: str,
    leave_type: str,
    requested_days: int,
    db: Optional[Dict[str, Dict[str, Any]]] = None
) -> Tuple[bool, int, str]:
    """
    Checks balance entitlement.
    If requested_days > available: returns Test Case 4 rejection format.
    """
    if db is None:
        db = employee_database

    balances = db[emp_id]["balances"]
    available = balances.get(leave_type, 0)

    if requested_days <= available:
        return True, available, "Sufficient balance."
    else:
        # Test Case 4 Specification Output
        return False, available, f"Leave rejected. Requested: {requested_days} days | Available: {available} days"


def apply_leave(
    emp_id_input: str,
    leave_type_input: str,
    from_date_input: str,
    to_date_input: str,
    db: Optional[Dict[str, Dict[str, Any]]] = None,
    sync_csv: bool = True
) -> Tuple[bool, str]:
    """
    Processes a complete leave application request:
    1. Validates employee ID
    2. Validates leave type
    3. Validates date order and format via datetime
    4. Computes inclusive days
    5. Checks leave balance sufficiency
    6. Decrements balance on approval; leaves balance unchanged on rejection.
    """
    if db is None:
        db = employee_database

    # Validate ID
    valid_id, emp_id, err_msg = validate_employee_id(emp_id_input, db)
    if not valid_id:
        return False, err_msg

    # Validate Leave Type
    valid_type, leave_type, err_msg = validate_leave_type(leave_type_input)
    if not valid_type:
        return False, err_msg

    # Validate Dates
    valid_dates, from_dt, to_dt, requested_days, err_msg = parse_and_validate_dates(
        from_date_input, to_date_input
    )
    if not valid_dates:
        return False, err_msg

    # Verify Entitlement Balance
    sufficient, available, balance_msg = check_leave_balance(
        emp_id, leave_type, requested_days, db
    )
    if not sufficient:
        log_leave_audit(emp_id, leave_type, from_date_input, to_date_input, requested_days, "REJECTED", available)
        return False, balance_msg

    # Deduct balance on approval
    db[emp_id]["balances"][leave_type] -= requested_days
    new_balance = db[emp_id]["balances"][leave_type]

    if sync_csv:
        save_employees_to_csv(db)
        log_leave_audit(emp_id, leave_type, from_date_input, to_date_input, requested_days, "APPROVED", new_balance)

    # Test Case 1 & 2 Specification Output
    approval_msg = f"Leave approved: {requested_days} days {leave_type} | Balance {leave_type}: {new_balance}"
    return True, approval_msg


def get_balance_string(
    emp_id_input: str,
    db: Optional[Dict[str, Dict[str, Any]]] = None
) -> Tuple[bool, str]:
    """
    Retrieves the formatted balance string for an employee.
    Test Case 4(b) Output: Casual: 12 | Sick: 10 | Earned: 15
    """
    if db is None:
        db = employee_database

    valid_id, emp_id, err_msg = validate_employee_id(emp_id_input, db)
    if not valid_id:
        return False, err_msg

    b = db[emp_id]["balances"]
    return True, f"Casual: {b['Casual']} | Sick: {b['Sick']} | Earned: {b['Earned']}"


def view_balance(
    emp_id_input: str,
    db: Optional[Dict[str, Dict[str, Any]]] = None
) -> None:
    """Displays the exact balance format required by Test Case 4(b)."""
    _, balance_str = get_balance_string(emp_id_input, db)
    print(balance_str)


# ==============================================================================
# Console User Interface Layer
# ==============================================================================

def display_menu() -> None:
    """Prints the application main menu."""
    print()
    print("========================================")
    print("    EMPLOYEE LEAVE MANAGEMENT SYSTEM")
    print("========================================")
    print("1. Apply for Leave")
    print("2. View Leave Balance")
    print("3. View All Employees")
    print("4. Exit")
    print("========================================")


def handle_apply_interactive() -> None:
    """Collects inputs and prints result for Option 1."""
    print()
    emp_id = input("Enter Employee ID: ").strip()
    leave_type = input("Enter Leave Type: ").strip()
    from_date = input("Enter From Date (YYYY-MM-DD): ").strip()
    to_date = input("Enter To Date (YYYY-MM-DD): ").strip()
    print()

    _, result = apply_leave(emp_id, leave_type, from_date, to_date)
    print(result)


def handle_view_balance_interactive() -> None:
    """Collects inputs and prints result for Option 2."""
    print()
    emp_id = input("Enter Employee ID: ").strip()
    print()
    view_balance(emp_id)


def handle_view_all_interactive() -> None:
    """Displays formatted table of all registered employees."""
    print()
    print("Registered Employee Leave Balances:")
    print(f"{'ID':<8} {'Name':<18} {'Department':<22} {'Balances'}")
    print("-" * 65)
    for emp_id, data in employee_database.items():
        b = data["balances"]
        b_str = f"Casual: {b['Casual']} | Sick: {b['Sick']} | Earned: {b['Earned']}"
        print(f"{emp_id:<8} {data['name']:<18} {data['department']:<22} {b_str}")
    print("-" * 65)


def run_automated_tests() -> None:
    """Executes the 4 official project specification test cases."""
    print("\nExecuting Built-in Specification Tests...")
    test_db = copy.deepcopy(DEFAULT_EMPLOYEES)

    # Test Case 1
    _, tc1 = apply_leave("E101", "Casual", "2026-12-10", "2026-12-12", test_db, sync_csv=False)
    assert tc1 == "Leave approved: 3 days Casual | Balance Casual: 9", f"TC1 Fail: {tc1}"

    # Test Case 2
    test_db = copy.deepcopy(DEFAULT_EMPLOYEES)
    _, tc2 = apply_leave("E101", "Casual", "2026-11-02", "2026-11-13", test_db, sync_csv=False)
    assert tc2 == "Leave approved: 12 days Casual | Balance Casual: 0", f"TC2 Fail: {tc2}"

    # Test Case 3
    test_db = copy.deepcopy(DEFAULT_EMPLOYEES)
    _, tc3 = apply_leave("E101", "Sick", "2026-12-15", "2026-12-10", test_db, sync_csv=False)
    assert tc3 == "Invalid dates. To-date cannot be before from-date.", f"TC3 Fail: {tc3}"

    # Test Case 4
    test_db = copy.deepcopy(DEFAULT_EMPLOYEES)
    _, tc4_a = apply_leave("E101", "Casual", "2027-01-01", "2027-01-14", test_db, sync_csv=False)
    _, tc4_b = get_balance_string("E101", test_db)
    assert tc4_a == "Leave rejected. Requested: 14 days | Available: 12 days", f"TC4a Fail: {tc4_a}"
    assert tc4_b == "Casual: 12 | Sick: 10 | Earned: 15", f"TC4b Fail: {tc4_b}"

    print("All 4 specification test cases verified successfully [PASS].\n")


def main() -> None:
    """CLI Entry point."""
    if len(sys.argv) > 1:
        arg = sys.argv[1].strip().lower()
        if arg in ("--test", "-t", "test"):
            run_automated_tests()
            return
        elif arg in ("--csv", "-c") and len(sys.argv) > 2:
            global employee_database
            employee_database = load_employees_from_csv(sys.argv[2])

    while True:
        display_menu()
        choice = input("Enter your choice (1-4): ").strip()

        if choice == "1":
            handle_apply_interactive()
        elif choice == "2":
            handle_view_balance_interactive()
        elif choice == "3":
            handle_view_all_interactive()
        elif choice == "4":
            print("\nExiting program. Thank you!")
            break
        else:
            print("\nInvalid choice. Please enter a number between 1 and 4.")


if __name__ == "__main__":
    main()
