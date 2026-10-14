# Security policy

## Scope

This policy covers the code in this repository: the FastAPI backend, the browser frontend, and the local secret vault module under `modules/local_secret_vault/`.

## Threat model

The dashboard is a local operator tool.

- The backend has no API authentication. Anyone who can reach its port can start and stop configured services and call the admin endpoints. Run it bound to `127.0.0.1` (the default in `start-dashboard.ps1`) and do not expose it to a network.
- Secrets are stored in a local vault under `runtime/vault`. Keys are derived with scrypt and values are encrypted with AES-GCM. The vault must be unlocked with a passphrase before secrets can be resolved.
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
