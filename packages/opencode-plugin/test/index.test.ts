import { describe, expect, it } from "vitest";
import { afterToolMetadata, governanceContextText, redactSecrets } from "../src/index.js";

describe("opencode governance plugin", () => {
  it("redacts known secret patterns", () => {
    expect(redactSecrets("Authorization: Bearer sk-123456789012345")).toContain("[REDACTED]");
  });

  it("injects concise governance context without policy internals", () => {
    const context = governanceContextText({
      taskId: "TASK-1",
      contractHash: "sha256:abc",
      allowedPaths: ["src"],
      protectedPaths: ["contract.json"]
    });
    expect(context).toContain("Final verdict is externally determined");
    expect(context).not.toContain("api_key");
  });

  it("redacts after tool execution metadata", () => {
    const metadata = afterToolMetadata("api_key=secretvalue", "", false);
    expect(metadata.stdout).toContain("[REDACTED]");
  });
});

