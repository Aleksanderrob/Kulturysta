"""Print verified public facts about the locally installed wbb-module."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hardware.wii_board_adapter import WiiBoardAdapter


def main() -> int:
    try:
        facts = WiiBoardAdapter.inspect_installed_api()
    except (ImportError, AttributeError, TypeError, ValueError) as exc:
        print(f"Nie można sprawdzić wbb-module: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(facts, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
