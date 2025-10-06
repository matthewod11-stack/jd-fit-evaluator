# Manual Tests

This directory contains manual and integration tests that require human verification or specific setup conditions.

## Files

- `test_cli.py` - Manual CLI testing and verification
- `test_manual_verification.py` - Manual verification workflows  
- `test_taxonomy.py` - Taxonomy and classification manual tests

## Running Manual Tests

These tests are not part of the automated test suite. Run them individually as needed:

```bash
# Run specific manual test
python tests/manual/test_cli.py

# Or run all manual tests
python -m pytest tests/manual/ -v
```

## Purpose

Manual tests serve different purposes than automated tests:

- End-to-end user workflows
- Visual/output verification
- Tests requiring human judgment
- Integration tests with external services
- Performance/stress testing scenarios

For automated unit and integration tests, see the main `tests/` directory.
