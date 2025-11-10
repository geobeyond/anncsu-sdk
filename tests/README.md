# ANNCSU SDK Test Suite

This directory contains the test suite for the ANNCSU SDK, created to verify the refactoring that extracted shared primitives into `anncsu.common`.

## Test Structure

```
tests/
├── common/
│   └── test_imports.py       # Tests for anncsu.common package imports (47 tests)
├── pa/
│   └── test_imports.py       # Tests for anncsu.pa package imports (28 tests)
├── integration/
│   └── test_sdk_instantiation.py  # Integration tests for SDK (24 tests)
├── conftest.py               # Pytest configuration
└── README.md                 # This file
```

## Test Coverage

### Common Package Tests (47 tests)

**File:** `tests/common/test_imports.py`

Tests that all shared primitives in `anncsu.common` can be imported correctly:

- **Package Structure** (2 tests)
  - Common package imports
  - Package path validation

- **Types Module** (7 tests)
  - BaseModel, Nullable, OptionalNullable
  - UNSET, UNSET_SENTINEL
  - UnrecognizedInt, UnrecognizedStr

- **Utils Module** (8 tests)
  - RetryConfig, BackoffStrategy
  - SerializedRequestBody
  - FieldMetadata, QueryParamMetadata, PathParamMetadata, HeaderMetadata

- **Errors Module** (7 tests)
  - AnncsuBaseError, APIError
  - NoResponseError, ResponseValidationError
  - Error inheritance hierarchy

- **Hooks Module** (3 tests)
  - SDKHooks
  - BeforeRequestContext, AfterSuccessContext, AfterErrorContext

- **Infrastructure** (4 tests)
  - HttpClient, AsyncHttpClient
  - BaseSDK, SDKConfiguration

- **Utility Modules** (16 tests)
  - Individual utility module imports
  - annotations, datetimes, enums, eventstreaming
  - forms, headers, logger, metadata
  - queryparams, requestbodies, retries, security
  - serializers, unmarshal_json_response, url, values

### PA Package Tests (28 tests)

**File:** `tests/pa/test_imports.py`

Tests that the PA-specific package works correctly and uses common primitives:

- **Package Structure** (2 tests)
  - PA package imports
  - Package path validation

- **SDK Imports** (2 tests)
  - Main Anncsu SDK class
  - SDK from module

- **Endpoint Imports** (4 tests)
  - Queryparam, JSONPost
  - Pathparam, Status

- **Models** (5 tests)
  - PA-specific models import
  - Model inheritance from common BaseModel

- **Errors** (4 tests)
  - PA error compatibility
  - Operation-specific errors

- **Common Integration** (3 tests)
  - PA uses common types
  - PA can import common utils
  - PA can import common errors

- **Backward Compatibility** (4 tests)
  - PA still has utils/types modules
  - Old import paths still work (Speakeasy compatibility)

- **Configuration** (2 tests)
  - SDKConfiguration from PA
  - BaseSDK from PA

- **Versioning** (2 tests)
  - Version info imports

### Integration Tests (24 tests)

**File:** `tests/integration/test_sdk_instantiation.py`

Tests that the SDK works end-to-end after refactoring:

- **SDK Instantiation** (6 tests)
  - Default instantiation
  - Correct attributes
  - Configuration setup
  - Custom server URL
  - Context manager support
  - Async context manager support

- **Retry Configuration** (2 tests)
  - SDK with retry config from common
  - RetryConfig import from common

- **Endpoint Access** (4 tests)
  - Queryparam endpoint accessible
  - JSONPost endpoint accessible
  - Pathparam endpoint accessible
  - Status endpoint accessible

- **Models Usage** (2 tests)
  - Request models instantiation
  - Models use common BaseModel

- **Error Handling** (3 tests)
  - AnncsuError can be caught
  - AnncsuBaseError accessible
  - APIError accessible

- **Namespace Package** (4 tests)
  - Anncsu namespace exists
  - Common subpackage accessible
  - PA subpackage accessible
  - Common and PA are separate

- **Cross-Package Imports** (3 tests)
  - PA uses common types
  - PA uses common utils
  - Common doesn't depend on PA

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Suite

```bash
# Common package tests
pytest tests/common/test_imports.py -v

# PA package tests
pytest tests/pa/test_imports.py -v

# Integration tests
pytest tests/integration/test_sdk_instantiation.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=anncsu --cov-report=html
```

## Test Results

**Total Tests:** 99  
**Status:** ✅ All Passing  
**Coverage:** 32% (focus on import paths, not implementation)

### Test Breakdown

| Test Suite | Tests | Status |
|------------|-------|--------|
| Common Imports | 47 | ✅ PASS |
| PA Imports | 28 | ✅ PASS |
| Integration | 24 | ✅ PASS |
| **Total** | **99** | **✅ PASS** |

## What These Tests Verify

### 1. Refactoring Correctness
- All shared primitives successfully moved to `anncsu.common`
- No circular import dependencies
- Proper package separation

### 2. Import Paths
- Common package exports correct modules
- PA package correctly imports from common
- Backward compatibility maintained

### 3. SDK Functionality
- SDK instantiates correctly
- All endpoints accessible
- Configuration works properly
- Context managers function

### 4. Type Safety
- Models inherit from correct base classes
- Error hierarchy preserved
- Type annotations maintained

### 5. Backward Compatibility
- Old import paths still work (for Speakeasy)
- No breaking changes for users
- Existing code continues to function

## Issues Found and Fixed

### Issue 1: Circular Import in SDKConfiguration
**Problem:** `anncsu.common.sdkconfiguration` importing from `anncsu.pa._version` caused circular dependency.

**Solution:** Implemented lazy loading with `__post_init__` method:
```python
def __post_init__(self):
    """Initialize version info lazily to avoid circular imports."""
    if self.openapi_doc_version is None:
        try:
            ver, openapi, gen, ua = _get_version_info()
            # Set version info
        except ImportError:
            # Use defaults
```

### Issue 2: Incorrect Import in pathparam.py
**Problem:** `from anncsu import errors, models, utils` instead of `from anncsu.pa import`.

**Solution:** Fixed to:
```python
from anncsu.pa import errors, models
from anncsu.common import utils
```

## Future Test Additions

When adding new API specifications, create similar test suites:

```
tests/
├── common/                    # Already exists
├── pa/                        # Already exists
├── aggiornamento_accessi/    # New API
│   └── test_imports.py
├── aggiornamento_coordinate/  # New API
│   └── test_imports.py
└── integration/
    └── test_all_apis.py       # Test all APIs work together
```

## CI/CD Integration

These tests should be run:
- On every commit (pre-commit hook)
- On every pull request
- Before every release

Recommended CI configuration:
```yaml
test:
  script:
    - pytest tests/ -v --cov=anncsu
    - pytest tests/ --cov=anncsu --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## Contributing

When adding new functionality:
1. Add corresponding import tests to appropriate suite
2. Update integration tests if SDK interface changes
3. Ensure all tests pass before submitting PR
4. Maintain or improve coverage percentage

## Notes

- Tests focus on **import correctness** rather than implementation details
- Implementation testing (API calls, business logic) should be in separate test files
- These tests verify the refactoring integrity
- Coverage of 32% is expected - we're testing structure, not implementation

---

**Created:** November 10, 2025  
**Purpose:** Verify refactoring that extracted shared primitives to anncsu.common  
**Status:** ✅ All tests passing
