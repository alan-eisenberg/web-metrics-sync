from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclass
class RunState:
    run_id: str
    state: str = "INIT"
    retries: dict[str, int] = field(default_factory=dict)
    email: str | None = None
    username: str | None = None
    current_prompt: int = 0
    preview_urls: list[str] = field(default_factory=list)
    last_error: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


def _atomic_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w", delete=False, dir=path.parent, encoding="utf-8"
    ) as tmp:
        json.dump(payload, tmp, indent=2)
        tmp.flush()
        temp_name = tmp.name
    Path(temp_name).replace(path)


def save_state(path: Path, state: RunState) -> None:
    _atomic_write(path, asdict(state))


def load_state(path: Path) -> RunState | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return RunState(**data)
