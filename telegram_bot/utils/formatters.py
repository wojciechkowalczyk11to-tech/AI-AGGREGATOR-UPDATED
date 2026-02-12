from __future__ import annotations
import re
_SPECIAL_CHARS = r'_*[]()~`>#+-=|{}.!'
_ESCAPE_RE = re.compile(f'([{re.escape(_SPECIAL_CHARS)}])')
def escape_markdown_v2(text: str) -> str:
    return _ESCAPE_RE.sub(r'\\\1', text) if text else ""
def safe_markdown_v2(text: str) -> str:
    if not text: return ""
    parts = []
    code_block_re = re.compile(r'(```[\s\S]*?```)')
    segments = code_block_re.split(text)
    for j, segment in enumerate(segments):
        if j % 2 == 1: parts.append(segment)
        else:
            inline_re = re.compile(r'(`[^`]+`)')
            inline_segments = inline_re.split(segment)
            for k, inline_seg in enumerate(inline_segments):
                if k % 2 == 1: parts.append(inline_seg)
                else: parts.append(escape_markdown_v2(inline_seg))
    return "".join(parts)
