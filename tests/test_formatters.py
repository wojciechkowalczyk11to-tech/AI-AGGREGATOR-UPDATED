from __future__ import annotations
from utils.formatters import escape_markdown_v2
def test_esc():
    assert escape_markdown_v2("a_b") == "a\\_b"
