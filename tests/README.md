# Tests Directory

This directory contains all test files, demo scripts, and test utilities for the OpenAI Usage Metrics Dashboard.

## Directory Structure

```
tests/
├── README.md                          # This file
├── test_*.py                          # Main test scripts
├── demos/                             # Demo and verification scripts
│   ├── demo_department_fix.py
│   ├── demo_employee_upload_fix.py
│   └── demo_validation_system.py
├── fixtures/                          # Test utilities and setup scripts
│   ├── setup_test_db.py              # Creates test database
│   └── create_test_weekly_data.py    # Generates test data
└── data/                              # Test data files
    └── test_employees.csv            # Sample employee data
```

## Running Tests

### Main Test Suites

**Comprehensive validation test suite:**
```bash
python tests/test_data_validation.py
```

**Critical fixes test suite:**
```bash
python tests/test_critical_fixes.py
```

### Running Individual Tests

All test scripts can be run from the repository root:

```bash
# Example: Run pagination tests
python tests/test_pagination.py

# Example: Run employee integration tests
python tests/test_employee_integration.py
```

## Test Categories

### Core Functionality Tests
- `test_data_validation.py` - Data validation system (9 tests)
- `test_critical_fixes.py` - Critical bug fixes verification (4 tests)
- `test_data_processor_weekly.py` - Weekly data processing

### Feature-Specific Tests
- `test_employee_integration.py` - Employee file integration
- `test_department_mapper_*.py` - Department mapping UI and deduplication
- `test_pagination*.py` - Pagination functionality
- `test_auto_load_employee.py` - Auto-load employee file on startup

### Integration Tests
- `test_integration_dept_mapper.py` - Department mapper integration
- `test_integration_weekly.py` - Weekly file processing integration
- `test_weekly_file_support.py` - Weekly file format support

### Bug Fix Verification Tests
- `test_power_user_department_fix.py` - Power user department assignment
- `test_unknown_dept_breakdown.py` - Unknown department handling
- `test_realistic_unknown_dept.py` - Unknown department edge cases
- `test_department_employee_fix.py` - Department-employee mapping
- `test_delete_employee.py` - Employee deletion feature
- `test_employee_upload_edge_cases.py` - Employee upload edge cases

## Demo Scripts

Located in `demos/`, these scripts demonstrate specific features and fixes:

- `demo_department_fix.py` - Department performance bug fix
- `demo_employee_upload_fix.py` - Employee upload fix visualization
- `demo_validation_system.py` - Data validation system demo

## Test Utilities

Located in `fixtures/`:

- `setup_test_db.py` - Creates a test database with sample data
- `create_test_weekly_data.py` - Generates weekly test data files

## Test Data

Located in `data/`:

- `test_employees.csv` - Sample employee data for testing employee integration features

## Notes

- All tests are designed to be run from the repository root directory
- Tests use relative paths to locate the main application code
- Some tests create temporary databases and files which are cleaned up automatically
- Tests do not require external dependencies beyond those in `requirements.txt`
