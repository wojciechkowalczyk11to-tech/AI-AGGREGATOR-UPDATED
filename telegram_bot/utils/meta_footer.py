from __future__ import annotations
def format_meta_footer(model, cost, tokens, elapsed, fallback_used=False) -> str:
    parts = [f"🤖 `{model}`", f"💳 `${cost:.4f}`", f"⚡ `{tokens}` tok", f"⏱ `{elapsed:.1f}s`"]
    if fallback_used: parts.append("⚠️ Fallback")
    return "\n\n───\n" + " | ".join(parts)
