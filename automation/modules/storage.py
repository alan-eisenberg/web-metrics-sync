from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile


def _atomic_write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w", delete=False, dir=path.parent, encoding="utf-8"
    ) as tmp:
        json.dump(payload, tmp, indent=2)
        tmp.flush()
        tmp_name = tmp.name
    Path(tmp_name).replace(path)


def load_credentials(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def upsert_credential(path: Path, entry: dict) -> None:
    items = load_credentials(path)
    for idx, current in enumerate(items):
        if current.get("email") == entry.get("email"):
            merged = {**current, **entry}
            items[idx] = merged
            _atomic_write_json(path, items)
            return
    items.append(entry)
    _atomic_write_json(path, items)
