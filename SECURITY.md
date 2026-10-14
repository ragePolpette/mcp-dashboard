# Security policy

## Scope

This policy covers the code in this repository: the FastAPI backend, the browser frontend, and the local secret vault module under `modules/local_secret_vault/`.

## Threat model

The dashboard is a local operator tool.

- The backend has no user authentication. Anyone who can reach its port can obtain the session token and then start and stop configured services and call the admin endpoints. Run it bound to `127.0.0.1` (the default in `start-dashboard.ps1`) and do not expose it to a network without an authenticating reverse proxy.
- Browser-based attacks from other sites are mitigated: the `Host` header must be in an allow-list (loopback by default, see `MCP_DASHBOARD_ALLOWED_HOSTS`), and state-changing requests need a same-origin `Origin`/`Referer` when present, the `X-Requested-With: mcp-dashboard` header and the per-process session token in `X-Dashboard-Token`.
- Secrets are stored in a local vault under `runtime/vault`. Keys are derived with scrypt and values are encrypted with AES-GCM. Vault files are written atomically with mode `0600`. The vault must be unlocked with a passphrase before secrets can be resolved, and it locks itself again after the configured idle timeout (30 minutes by default).
- Vault reference names cannot contain path separators, colons or `..`, and every ciphertext path is checked to stay inside the vault store.
- Secrets are passed to managed services as environment variables when they start. Locking the vault does not remove them from already running processes. Stop the service to clear them.
- The UI and API do not return stored secret values in cleartext.
- Services are launched from commands defined in `backend/config/services.json`. Treat that file as trusted input.

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub Security Advisories for this repository ("Report a vulnerability" under the Security tab). If that is not available, open an issue asking for a private contact channel, without including details.

Include the affected commit or version, reproduction steps, and the impact you observed. Never include real credentials.

## Not covered

- Deployments exposed to untrusted networks without an external authentication layer
- An attacker who already has access to the user account, the filesystem, or process memory on the host
- Vulnerabilities in managed MCP services or in third-party dependencies, which should be reported to their own projects
- Misconfiguration of `services.json` or of the databases that SQL targets point to
