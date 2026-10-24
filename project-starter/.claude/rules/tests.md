---
paths:
  - "**/*.test.*"
  - "**/*.spec.*"
  - "**/test_*.py"
  - "**/*_test.py"
  - "tests/**"
  - "e2e/**"
---

# Tests

- A test describes behaviour the owner asked for, in GLOSSARY.md terms. Name it after that behaviour, not the function.
- Never delete, skip (`.skip`, `.only`, `xit`, `@pytest.mark.skip`) or loosen a failing test to make the suite pass. Fix the code, or stop and report.
- Test through the public interface. Mock only what crosses the process boundary (network, clock, external APIs).
- For money or tax calculations, use exact expected values from a worked example the owner confirmed, never values copied from the code's own output.
