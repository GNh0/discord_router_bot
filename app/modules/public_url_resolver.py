from __future__ import annotations

import re
from pathlib import Path


class PublicUrlResolver:
    def __init__(self, url_file: str, tunnel_log_file: str) -> None:
        self.url_file = url_file
        self.tunnel_log_file = tunnel_log_file
        self._quick_tunnel_re = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", flags=re.IGNORECASE)

    def extract_from_text(self, text: str) -> str:
        match = self._quick_tunnel_re.search(text or "")
        return match.group(0) if match else ""

    def read(self) -> str:
        direct = self._read_url_file()
        if direct:
            return direct
        return self._read_from_log()

    def _read_url_file(self) -> str:
        path = Path(self.url_file)
        if not path.exists():
            return ""
        try:
            return path.read_text(encoding="utf-8").strip()
        except Exception:
            return ""

    def _read_from_log(self) -> str:
        path = Path(self.tunnel_log_file)
        if not path.exists():
            return ""
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            return ""
        return self.extract_from_text(text)
