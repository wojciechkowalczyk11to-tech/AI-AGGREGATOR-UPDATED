from __future__ import annotations

from utils.meta_footer import format_meta_footer


def test_foot():
    assert "🤖" in format_meta_footer("m", 0, 0, 0)
