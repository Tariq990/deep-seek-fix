# Task Contract

Task contracts use a versioned Pydantic model with canonical JSON serialization and a locally recomputed SHA-256 hash. The hash excludes the `contract_hash` field itself.

Unknown schema versions, malformed fields, unsafe relative paths, and overlaps between allowed and protected paths fail validation.

