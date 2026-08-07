# Smoke Tests

End-to-end tests that exercise the `robotframework-radkit` library against a live RADKit service.

## Prerequisites

1. **Install the package with the `genie` extra:**

   ```bash
   uv pip install -e ".[genie]"
   ```

   The test wrapper will automatically install additional dependencies (`unicon`, `pyats.robot`)
   matching the installed genie major version.

2. **Set required environment variables:**

   ```bash
   export RADKIT_IDENTITY=<path-to-identity-file>
   export RADKIT_CLIENT_PRIVATE_KEY_PASSWORD=<private-key-password>
   ```

   The tests will refuse to run if these are not set.

3. **Configure test variables:**

   Copy the example variables file and adjust for your environment:

   ```bash
   cp smoke_variables.yaml.example smoke_variables.yaml
   ```

   Edit `smoke_variables.yaml` to point at your RADKit service, devices, etc.
   This file is gitignored and will not be committed.

## Running

Via pytest:

```bash
pytest tests/smoke/test_smoke.py
```

Or directly:

```bash
python tests/smoke/test_smoke.py
```

Both methods will:
- Verify the `genie` package is installed
- Install `unicon` and `pyats.robot` (matching the genie major version) via `uv pip`
- Check that required environment variables are set
- Run `test_smoke.robot` and report results

## Output

Robot Framework output (log.html, report.html, output.xml) is written to `tests/smoke/robot_output/`.

## Test Structure

| File | Purpose |
|------|---------|
| `test_smoke.py` | Pytest wrapper handling deps, env checks, and robot invocation |
| `test_smoke.robot` | Robot Framework test suite (client, genie, port-forwarding) |
| `smoke_variables.yaml.example` | Template for test variables |
| `smoke_variables.yaml` | Your local test variables (gitignored) |
| `testbed.yaml` | pyATS testbed topology |
