# aida_bot/memory.py
from datetime import datetime
from typing import Literal, List, Dict, Any
from aida_bot.storage.database import get_storage_client

Role = Literal["user", "assistant", "system"]

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _db(storage=None):
    return storage or get_storage_client()

def ensure_profile(user_id: int, display_name: str | None = None, extra: dict | None = None, storage=None) -> dict:
    db = _db(storage)
    profile = db.get_profile(user_id) or {}
    if display_name:
        profile["displayName"] = display_name
    if extra:
        profile.update(extra)
    db.save_profile(user_id, profile)
    return profile

def get_history(user_id: int, storage=None) -> List[Dict[str, Any]]:
    db = _db(storage)
    session = db.get_session(user_id)
    return session.get("history", [])

def save_turn(user_id: int, role: Role, text: str, cap: int = 12, storage=None) -> List[Dict[str, Any]]:
    db = _db(storage)
    session = db.get_session(user_id)
    history: List[Dict[str, Any]] = session.get("history", [])
    history.append({"role": role, "text": text, "ts": _now_iso()})
    if len(history) > cap:
        history = history[-cap:]
    db.save_session(user_id, {"history": history, "updatedAt": _now_iso()})
    return history

def clear_history(user_id: int, storage=None):
    db = _db(storage)
    db.save_session(user_id, {"history": [], "updatedAt": _now_iso()})

def build_llm_context(user_id: int, extra_facts: dict | None = None, storage=None) -> str:
    db = _db(storage)
    profile = db.get_profile(user_id) or {}
    history = get_history(user_id, storage=db)

    facts_lines = []
    for k, v in profile.items():
        if k in ("displayName", "idioma", "preferencias", "autonomia", "foco", "entorno"):
            facts_lines.append(f"- {k}: {v}")
    if extra_facts:
        for k, v in extra_facts.items():
            facts_lines.append(f"- {k}: {v}")

    hist_lines = [f'{m["role"].upper()}: {m["text"]}' for m in history]

    return (
        "Hechos persistentes del usuario:\n" +
        ("\n".join(facts_lines) if facts_lines else "- (sin datos)") +
        "\n\nHistoria reciente:\n" +
        ("\n".join(hist_lines) if hist_lines else "(sin historial)")
    )
