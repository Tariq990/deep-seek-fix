# OpenCode Integration

The OpenCode plugin under `packages/opencode-plugin` intercepts tool execution lifecycle events. It denies tool execution when the control plane is unavailable, malformed, or returns an unknown policy decision.

Install by linking the workspace package into `.opencode/plugins/` and referencing it from `opencode.json` during development.

