from __future__ import annotations

from pathlib import Path


def load_guard_script(js_dir: Path) -> str:
    script_path = js_dir / "auto_regenerate.js"
    return script_path.read_text(encoding="utf-8")
