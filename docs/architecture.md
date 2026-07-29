# Architecture

Deep Seek Fix separates proposal, authorization, execution, evidence, and delivery.

The agent may propose a command. The local policy engine evaluates the structured request. The executor captures local process results into an append-only SQLite ledger. Claims are then verified against fresh evidence tied to the current contract hash, repository head, working-tree hash, and environment fingerprint.

