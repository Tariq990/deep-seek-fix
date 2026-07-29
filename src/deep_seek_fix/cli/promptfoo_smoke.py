from pathlib import Path

import yaml


def main() -> None:
    config_path = Path("evals/promptfoo/promptfooconfig.yaml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    tests = config.get("tests", [])
    if len(tests) < 10:
        raise SystemExit("promptfoo smoke requires at least 10 deterministic tests")


if __name__ == "__main__":
    main()
