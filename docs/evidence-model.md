# Evidence Model

Evidence records are append-only SQLite rows containing command metadata, hashes of redacted output, repository head SHA, working-tree hash, environment hash, and timestamps.

Evidence is fresh only when it matches the current contract hash, repository state, working-tree state, and environment fingerprint.

