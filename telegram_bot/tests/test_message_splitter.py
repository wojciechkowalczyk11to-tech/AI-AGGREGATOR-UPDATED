from __future__ import annotations
from utils.message_splitter import split_message
def test_split():
    assert len(split_message("a"*5000)) > 1
