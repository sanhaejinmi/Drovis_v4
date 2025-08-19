import json, os, time
from pathlib import Path
from typing import List, Dict, Any, Optional

APP_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = APP_ROOT / "data"
HISTORY_PATH = str(DATA_DIR / "history.json")

def _read() -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []
    
def _write(data: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    tmp = HISTORY_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, HISTORY_PATH)


def load_all(username: Optional[str] = None) -> List[Dict[str, Any]]:
    data = _read()
    if username is None:
        return data
    return [d for d in data if d.get("username") == username]


def append_record(item: Dict[str, Any]) -> None:
    data = _read()
    item.setdefault("id", int(time.time() * 1000))
    data.append(item)
    _write(data)


def delete_all(username: Optional[str] = None) -> int:
    data = _read()
    if username is None:
        remained = []
    else:
        remained = [d for d in data if d.get("username") != username]
    deleted = len(data) - len(remained)
    _write(remained)
    return deleted


# 필요 시
#def delete_one(record_id: int) -> bool:
#    data = _read()
#    new = [d for d in data if d.get("id") != record_id]
#    ok = len(new) != len(data)
#    if ok:
#        _write(new)
#    return ok