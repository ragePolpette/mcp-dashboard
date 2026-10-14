# SQL connections from the dashboard

This page describes the SQL target workflow in the `llm-sql-db-mcp` advanced panel.

## Creating a target

In **LLM SQL DB MCP > Advanced > DB Targets** you can create multiple DEV, QA or PROD targets. New targets start disabled and without write access.

1. Save the target.
2. Initialize or unlock the Vault.
3. Fill in the SQL Server connection form: server (or instance), optional port, database, SQL user and password. From a container, a SQL Server running on the Windows host can be reached with `host.docker.internal`.

The form supports SQL authentication. TLS is enabled and certificate verification stays on by default. The password is encrypted in the Vault under a reference dedicated to the target and is not returned by the endpoint. When editing, an empty password keeps the stored one. A connection that uses advanced options the form cannot represent remains editable from the Vault and is not rewritten automatically. Manual references remain available under Advanced.

## Applying changes

After saving connection, state and policy, press **Apply to SQL server**. This validates the active references and restarts only `llm-sql-db-mcp`. Running MCP sessions are interrupted by the restart.

- The Vault must be unlocked to apply active targets.
- For PROD targets with anonymization enabled, the anonymization salt must also be set in the service options.
- Saving a target and a healthy service state do not verify database connectivity. No test query is executed.
- Locking the Vault does not remove credentials from processes that are already running. Stop the SQL service to clear them from its memory.

## Anonymization

Anonymization is configurable for PROD as well. Disabling it returns the original data on reads. PROD writes remain disabled. Save the target and press **Apply to SQL server** for the change to take effect.

## Tests

Automated checks use synthetic data only:

```bash
python -m pytest -q
```
