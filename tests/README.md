# 🧪 Testing Guide - OnCall Runbook RAG System

## Overview

This directory contains comprehensive tests for the OnCall Runbook RAG System, covering all major functionality as specified in Prompt 14.

## Test Categories

### 1. **KB Persistence Tests**
- `test_kb_persist`: Tests document ingestion → status ready → ensure_index → still ready
- Verifies that the knowledge base maintains state across operations

### 2. **Anti-Generic Gate Tests**
- `test_no_generic_when_sufficient`: Tests quality gate passes with sufficient content
- `test_missing_context_message`: Tests missing context message generation
- Ensures answer quality standards are enforced

### 3. **Session Management Tests**
- `test_sessions_persist`: Tests session creation and message persistence
- Verifies chat history is maintained across requests

### 4. **Citation Quality Tests**
- `test_citations_clean`: Tests citation normalization, de-duplication, and filtering
- Ensures meta files (README, LICENSE, CHANGELOG) are excluded

### 5. **Domain-Specific Scenario Tests**
- `test_cpu_spike_no_fix_section`: CPU issues with only diagnostic steps
- `test_db_pool_has_fix_validate`: Database pool with fix and validation steps
- `test_cache_hotkey_specific`: Cache management with specific settings
- `test_queue_backlog_specific`: Queue scaling with specific parameters

## Running Tests

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure API service is running
make up
```

### Run All Tests
```bash
# Using Makefile
make test

# Using pytest directly
cd api
python -m pytest ../tests/ -v

# Using test runner script
python run_tests.py
```

### Run Specific Test Categories
```bash
# Run only unit tests
pytest tests/ -m unit -v

# Run only integration tests
pytest tests/ -m integration -v

# Run specific test file
pytest tests/test_rag_system.py::TestRAGSystem::test_kb_persist -v
```

## Test Configuration

### Pytest Configuration (`pytest.ini`)
- Verbose output (`-v`)
- Short traceback format (`--tb=short`)
- Disable warnings (`--disable-warnings`)
- Custom markers for test categorization

### Test Fixtures (`conftest.py`)
- `test_data_dir`: Temporary test data directory
- `test_docs_dir`: Test documents directory
- `test_index_dir`: Test FAISS index directory
- `test_db_path`: Test database path
- `mock_environment`: Mocked environment variables

## Test Data

Tests create temporary documents with realistic content:
- Incident response guides
- Troubleshooting manuals
- Performance tuning guides
- Database management docs
- Cache configuration guides
- Queue management procedures

## Mocking Strategy

- **FAISS Service**: Mocked to return controlled search results
- **Environment Variables**: Mocked for consistent testing
- **File System**: Uses temporary directories
- **Database**: Uses test database files

## Expected Test Results

### All Tests Should Pass
- ✅ KB persistence maintained
- ✅ Quality gates enforced appropriately
- ✅ Sessions persist correctly
- ✅ Citations cleaned and normalized
- ✅ Domain-specific scenarios handled

### Selfcheck Endpoint
- ✅ KB status verification
- ✅ FAISS index health check
- ✅ Database connectivity
- ✅ Minimal ingest if needed
- ✅ Sample RAG queries

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the API directory
   cd api
   python -m pytest ../tests/
   ```

2. **Path Issues**
   ```bash
   # Check test data directories exist
   ls -la tests/
   ```

3. **Service Dependencies**
   ```bash
   # Ensure API service is running
   make health
   ```

### Debug Mode
```bash
# Run with debug output
pytest tests/ -v -s --tb=long

# Run single test with debug
pytest tests/test_rag_system.py::TestRAGSystem::test_kb_persist -v -s
```

## Continuous Integration

Tests are designed to run in CI/CD environments:
- No external dependencies
- Deterministic results
- Fast execution
- Clear pass/fail criteria

## Coverage

Tests cover:
- ✅ Core RAG functionality
- ✅ Document processing
- ✅ Quality enforcement
- ✅ Session management
- ✅ Citation handling
- ✅ Domain-specific scenarios
- ✅ System health checks

## Adding New Tests

1. **Follow Naming Convention**: `test_<feature_name>`
2. **Use Descriptive Names**: Clear what is being tested
3. **Include Assertions**: Verify expected behavior
4. **Add Documentation**: Explain test purpose
5. **Use Fixtures**: Leverage existing test infrastructure

## Performance

- **Test Execution**: < 30 seconds for full suite
- **Memory Usage**: < 100MB per test
- **Disk Usage**: Temporary files cleaned automatically
- **Network**: No external calls (fully mocked)

