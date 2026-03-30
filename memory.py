"""
memory.py — Persistent memory for the Autonomous Cognitive Engine.
Stores full reports + todos per topic. Fuzzy deduplication prevents bloat.
"""
import json, os

# Always resolve relative to this file's directory — works regardless of CWD
MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")


_STOPWORDS = {"a", "an", "the", "of", "in", "on", "for", "to", "and", "or",
              "is", "are", "was", "were", "its", "with", "by", "at", "from"}


def _keywords(text: str) -> set:
    """Lowercase words with stopwords removed for better overlap matching."""
    return {w for w in text.lower().split() if w not in _STOPWORDS and len(w) > 2}


def search_memory(query: str) -> list:
    """Return all memory entries whose topic has >35% keyword overlap with query."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    query_words = _keywords(query)
    if not query_words:
        return []

    results = []
    for item in data:
        topic_words = _keywords(item.get("topic", ""))
        if not topic_words:
            continue
        overlap = len(query_words & topic_words) / max(len(query_words), len(topic_words))
        if overlap >= 0.35:
            results.append(item)
    return results


def save_memory(entry: dict) -> None:
    """Save entry to memory. Updates existing entry if topic keyword overlap >= 55%."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = []
    else:
        data = []

    new_words = _keywords(entry.get("topic", ""))

    for item in data:
        existing_words = _keywords(item.get("topic", ""))
        if not existing_words:
            continue
        overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))
        if overlap >= 0.55:
            item["summary"] = entry.get("summary", item.get("summary", ""))
            item["todos"]   = entry.get("todos",   item.get("todos", []))
            item["topic"]   = entry.get("topic",   item.get("topic", ""))
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return

    data.append(entry)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
