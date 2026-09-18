# Any bytes and multi-target validation — 2026-09-18

Max Result Bytes accepts a positive integer or `Any`. The API and runtime export
represent Any as JSON `null`; absent values retain the 131072-byte default.
This does not remove Max Rows, SQL timeouts, memory or client transport limits.
Existing targets keep their current numeric limits until explicitly changed.

Target IDs are unique stable identifiers using ASCII letters, digits, `_`, `-`,
and `.`, starting with a letter/digit. Display names may include spaces, accents
and punctuation and may be edited independently. There is no configured target
count cap; this is not a claim of unlimited resources or a load benchmark.

Regression coverage uses 103 synthetic targets, including `client-a`, `client_a`
and `CLIENT-A`. New automatic connection environment names encode the exact ID
to avoid punctuation/case collisions. Existing names are retained; duplicate
bindings are rejected rather than routing another target's credentials.

Fixed flat form fields losing to persisted nested settings, empty tool lists
being replaced by defaults, and retained independent target drafts/race guards.
Tests cover creation, duplicate rejection, update, display rename, deletion,
reload, runtime export, API null roundtrip, separate limits, read/write policy,
anonymization/provider/model and Vault references. Production writes remain denied.

Validation in an isolated Docker image with `--network none`:

- Dashboard Python suite: 87 passed.
- Frontend navigation/isolation/normalization: 8 passed.
- Companion SQL suite: 81 passed, including null schema loading, large multibyte
  rows, numeric byte boundaries, post-anonymization byte clamping and independent
  row limits in the real driver with a synthetic pool.

No real database query or write is part of these tests. No browser visual test
was performed. Existing Python deprecation/cache-permission warnings are nonfatal.
SQL legacy environment overrides that ambiguously map to multiple target IDs
are rejected. SQL registry getters return deep copies so caller mutation cannot
change stored tool permissions.
