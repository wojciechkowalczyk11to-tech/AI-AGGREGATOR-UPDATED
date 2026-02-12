from __future__ import annotations

SAFE_LIMIT = 4000


def split_message(text: str, limit: int = SAFE_LIMIT) -> list[str]:
    if not text:
        return [""]
    if len(text) <= limit:
        return [text]
    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        split_at = limit
        triple_count = remaining[:split_at].count("```")
        if triple_count % 2 == 1:
            last_open = remaining.rfind("```", 0, split_at)
            if last_open > 0:
                split_at = last_open
        for sep in ["\n\n", "\n", ". ", "! ", "? ", ", ", " "]:
            pos = remaining.rfind(sep, 0, split_at)
            if pos > limit // 2:
                split_at = pos + len(sep)
                break
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    return chunks


def should_send_as_file(text: str) -> bool:
    return len(text) > 8000 or (text.count("```") >= 4 and len(text) > 6000)
