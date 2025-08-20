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

def load_evidence_by_decision(decision_id: str) -> Dict[str, Any]:
    """
    history.json에서 주어진 decision_id에 해당하는 evidence를 찾아 반환.
    못 찾으면 {} 반환(앱이 템플릿 설명으로 폴백 가능).
    레코드 형태는 두 가지를 모두 허용:
      - {"decision_id": "...", "evidence": {...}, ...}
      - {"id": 1724134312345, "evidence": {...}, ...}  # 숫자 id만 있는 경우
    """
    if not decision_id:
        return {}

    data = _read()  # List[Dict]
    if not isinstance(data, list):
        return {}

    # 1) decision_id 키로 직접 매칭
    for rec in data:
        if not isinstance(rec, dict):
            continue
        if str(rec.get("decision_id")) == str(decision_id):
            ev = rec.get("evidence")
            return ev if isinstance(ev, dict) else (rec if isinstance(rec, dict) else {})

    # 2) 혹시 숫자 id를 decision_id로 넘기는 케이스도 허용
    for rec in data:
        if not isinstance(rec, dict):
            continue
        if str(rec.get("id")) == str(decision_id):
            ev = rec.get("evidence")
            return ev if isinstance(ev, dict) else (rec if isinstance(rec, dict) else {})

    return {}


# 필요 시
#def delete_one(record_id: int) -> bool:
#    data = _read()
#    new = [d for d in data if d.get("id") != record_id]
#    ok = len(new) != len(data)
#    if ok:
#        _write(new)
#    return ok


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