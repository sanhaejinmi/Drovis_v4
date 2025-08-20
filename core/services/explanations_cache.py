# core/services/explanations_cache.py
import json, os

CACHE_FILE = "data/explanations_cache.json"

def _load():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _save(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_cached(decision_id):
    cache = _load()
    return cache.get(decision_id)

def set_cached(decision_id, payload):
    cache = _load()
    if payload is None:
        cache.pop(decision_id, None)
    else:
        cache[decision_id] = payload
    _save(cache)
