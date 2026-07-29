# Evidence Model

Evidence records are append-only SQLite rows containing command metadata, hashes of redacted output, repository head SHA, working-tree hash, environment hash, and timestamps.

Evidence is fresh only when it matches the current contract hash, repository state, working-tree state, and environment fingerprint.

The ledger stores bounded redacted stdout and stderr snapshots alongside output hashes. Claim verification uses these snapshots to reject zero-test success, truncated test evidence, and required-test claims where the required node IDs are absent from the command or output.
