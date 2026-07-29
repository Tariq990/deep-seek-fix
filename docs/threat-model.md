# Threat Model

Protected assets include task contracts, policy definitions, evidence stores, gate implementations, repository history, provider credentials, and private source code.

Threat actors include unreliable agents, malicious prompts, compromised tool output, dependency failure, policy engine failure, stale context, and accidental operator misuse.

Key risks:

- Prompt injection tells the model to bypass gates or hide failures.
- Command bypass uses shell chaining, nested shells, `--no-verify`, force-push, amend, or destructive commands.
- Stale evidence is reused after contract, code, environment, or working-tree changes.
- Tests are deleted, skipped, weakened, or reported as successful with zero executed tests.
- Secrets appear in model, tool, tracing, or provider output.
- Provider responses are empty, malformed, partial, or malicious.
- CI and Git hooks are bypassed or misclassified.

The default response to missing or malformed security-sensitive fields is `DENY`.

