import json, os, time
from pathlib import Path
from typing import List, Dict, Any, Optional

APP_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = APP_ROOT / "data"
HISTORY_PATH = str(DATA_DIR / "history.json")


# ---------- low-level IO ----------
def _read() -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []

def _write(data: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    tmp = HISTORY_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, HISTORY_PATH)


# ---------- public APIs ----------
def load_all(username: Optional[str] = None) -> List[Dict[str, Any]]:
    data = _read()
    if username is None:
        return data
    return [d for d in data if d.get("username") == username]

def append_record(item: Dict[str, Any]) -> None:
    """
    item 예시:
    {
      "username": "alice",
      "filename": "test.mp4",
      "pose_stats": {...},
      "result_per_chunk": [...],
      "result": "중",
      "behavior_probs_pct": {...},
      "timestamp": "2025-08-20 14:00:00",
      "evidence": [  # ★ 반드시 리스트
        {"label":"Loitering","timestamp_sec":12.8,"image_path":"uploads/.../L_000123.jpg"},
        ...
      ],
    }
    """
    data = _read()
    item = dict(item)  # defensive copy

    # id/username/evidence 기본값 보정
    item.setdefault("id", int(time.time() * 1000))
    if "username" not in item:
        item["username"] = None
    if not isinstance(item.get("evidence"), list):
        item["evidence"] = []

    data.append(item)
    _write(data)

def delete_all(username: Optional[str] = None) -> int:
    data = _read()
    remained = [] if username is None else [d for d in data if d.get("username") != username]
    deleted = len(data) - len(remained)
    _write(remained)
    return deleted

def load_evidence_by_decision(decision_id: str) -> List[Dict[str, Any]]:
    """
    decision_id 또는 숫자 id로 레코드를 찾아 evidence 리스트 반환.
    못 찾으면 [].
    """
    if not decision_id:
        return []
    data = _read()
    # 1) decision_id 매칭
    for rec in data:
        if str(rec.get("decision_id")) == str(decision_id):
            ev = rec.get("evidence")
            return ev if isinstance(ev, list) else []
    # 2) 숫자 id 매칭 허용
    for rec in data:
        if str(rec.get("id")) == str(decision_id):
            ev = rec.get("evidence")
            return ev if isinstance(ev, list) else []
    return []