"""
Minimal imghdr shim for Python 3.13+ to satisfy libraries expecting stdlib imghdr.
Implements imghdr.what(file, h=None) for a few common formats.
"""
from __future__ import annotations
from typing import Optional


def what(file, h: Optional[bytes] = None) -> Optional[str]:
    data: bytes
    if h is None:
        try:
            with open(file, "rb") as f:
                data = f.read(32)
        except Exception:
            return None
    else:
        data = h
    if len(data) < 10:
        return None
    # JPEG
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    # GIF
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    # WebP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    # BMP
    if data[:2] == b"BM":
        return "bmp"
    return None