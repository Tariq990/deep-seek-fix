export type PolicyEffect = "ALLOW" | "DENY" | "REQUIRE_APPROVAL";

export interface GovernanceContext {
  taskId: string;
  contractHash: string;
  allowedPaths: string[];
  protectedPaths: string[];
}

export interface ToolRequest {
  command: string[];
  cwd: string;
  writes: string[];
  network: boolean;
}

export interface PolicyResponse {
  effect: PolicyEffect;
  reasons: string[];
  normalized_command: string;
}

const SECRET_PATTERNS = [
  /(authorization:\s*bearer\s+)[A-Za-z0-9._-]+/gi,
  /(api[_-]?key\s*[=:]\s*)[A-Za-z0-9._-]+/gi,
  /\b(sk-[A-Za-z0-9_-]{12,})\b/g,
  /\b(gh[pousr]_[A-Za-z0-9_]{20,})\b/g
];

export function redactSecrets(value: string): string {
  return SECRET_PATTERNS.reduce((current, pattern) => {
    return current.replace(pattern, (_match: string, prefix?: string) => `${prefix ?? ""}[REDACTED]`);
  }, value);
}

export function governanceContextText(context: GovernanceContext): string {
  return [
    `Active task ID: ${context.taskId}`,
    `Contract hash: ${context.contractHash}`,
    `Allowed paths: ${context.allowedPaths.join(", ")}`,
    `Protected paths: ${context.protectedPaths.join(", ")}`,
    "Final verdict is externally determined.",
    "Report INCOMPLETE or BLOCKED when evidence is missing.",
    "Do not claim PASS yourself."
  ].join("\n");
}

export async function evaluateBeforeTool(
  controlPlaneUrl: string,
  request: ToolRequest
): Promise<PolicyResponse> {
  let response: Response;
  try {
    response = await fetch(new URL("/v1/policy/evaluate", controlPlaneUrl), {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(request)
    });
  } catch {
    return {
      effect: "DENY",
      reasons: ["control plane unavailable"],
      normalized_command: request.command.join(" ")
    };
  }

  if (!response.ok) {
    return {
      effect: "DENY",
      reasons: [`control plane returned HTTP ${response.status}`],
      normalized_command: request.command.join(" ")
    };
  }
  const payload = (await response.json()) as Partial<PolicyResponse>;
  if (
    payload.effect !== "ALLOW" &&
    payload.effect !== "DENY" &&
    payload.effect !== "REQUIRE_APPROVAL"
  ) {
    return {
      effect: "DENY",
      reasons: ["malformed policy response"],
      normalized_command: request.command.join(" ")
    };
  }
  return {
    effect: payload.effect,
    reasons: payload.reasons ?? [],
    normalized_command: payload.normalized_command ?? request.command.join(" ")
  };
}

export function afterToolMetadata(stdout: string, stderr: string, truncated: boolean) {
  return {
    stdout: redactSecrets(stdout),
    stderr: redactSecrets(stderr),
    truncated
  };
}

