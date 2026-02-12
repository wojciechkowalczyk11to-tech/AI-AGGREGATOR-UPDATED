from __future__ import annotations

import os

from pydub import AudioSegment


def convert_ogg_to_wav(ogg, wav):
    try:
        AudioSegment.from_file(ogg, format="ogg").export(wav, format="wav")
        return True
    except Exception:
        return False


def cleanup_files(*paths):
    for p in paths:
        if os.path.exists(p):
            os.remove(p)
