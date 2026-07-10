from __future__ import annotations

_text_mode = False


def set_text_mode(enabled: bool) -> None:
    global _text_mode
    _text_mode = enabled


def is_text_mode() -> bool:
    return _text_mode
