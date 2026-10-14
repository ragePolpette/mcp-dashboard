# Contributing

## Workflow

1. Fork the repository or create a branch from `main`.
2. Keep each branch focused on one change.
3. Add or update tests for behavior changes.
4. Open a pull request against `main` and fill in the template.

## Running tests

```bash
pip install -r backend/requirements.txt pytest httpx
python -m pytest -q
node --test tests/*.cjs
```

Tests must run without external services and use synthetic data only. CI runs the same commands on Python 3.11 and Node 22. No linter is configured.

## Security rules

- Never commit secrets, credentials, real `.env` files, or the contents of `runtime/`.
- Do not use real hostnames, connection strings, or customer data in tests, fixtures, or documentation.
- Do not return secret values in cleartext from API responses.
- Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).
