from __future__ import annotations

def route(user_text: str) -> str:
    t = (user_text or "").strip().lower()
    if any(k in t for k in ["streamlit", "secrets", "variave", "limit", "quota", "gemini"]):
        return "HELP"
    return "CHAT"
