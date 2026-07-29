# Harbor Adapter

This adapter defines deterministic reliability scenarios for Deep Seek Fix. The smoke dataset uses a fake provider and does not require live provider keys.

Primary metric: `false_pass_rate`. Any false `PASS` is a critical failure.

Future providers can be added by mapping DeepSeek, GLM/Z.ai, Qwen, Kimi, or MiniMax configurations into provider metadata while keeping the deterministic grader unchanged.

