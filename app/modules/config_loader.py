from __future__ import annotations

import configparser
import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


def _to_bool(value: str | bool | None, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | int | None, default: int = 0) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return default


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        return data
    return {}


def _load_ini(path: Path) -> dict[str, Any]:
    parser = configparser.ConfigParser()
    parser.read(path, encoding="utf-8-sig")

    bot: dict[str, Any] = {}
    if parser.has_section("bot"):
        bot["channel_id"] = _to_int(parser.get("bot", "channel_id", fallback="0"), 0)
        bot["announce_on_startup"] = _to_bool(parser.get("bot", "announce_on_startup", fallback="true"), True)
        bot["poll_seconds"] = _to_int(parser.get("bot", "poll_seconds", fallback="20"), 20)

    services: list[dict[str, Any]] = []
    channels: list[dict[str, Any]] = []

    for section in parser.sections():
        if section.startswith("service:"):
            key = section.split(":", 1)[1].strip()
            services.append(
                {
                    "key": key,
                    "command": parser.get(section, "command", fallback=key).strip(),
                    "label": parser.get(section, "label", fallback=key).strip(),
                    "url_file": parser.get(section, "url_file", fallback="").strip(),
                    "tunnel_log_file": parser.get(section, "tunnel_log_file", fallback="").strip(),
                }
            )
        elif section.startswith("channel:"):
            ch = _to_int(section.split(":", 1)[1].strip(), 0)
            modules_raw = parser.get(section, "modules", fallback="url_router").strip()
            mods = []
            for name in [x.strip() for x in modules_raw.split(",") if x.strip()]:
                mods.append({"name": name, "settings": {}})
            if ch > 0:
                channels.append({"id": ch, "modules": mods})

    return {"bot": bot, "services": services, "channels": channels}


def _load_xml(path: Path) -> dict[str, Any]:
    root = ET.fromstring(path.read_text(encoding="utf-8-sig"))
    bot = {
        "channel_id": _to_int(root.findtext("./bot/channel_id"), 0),
        "announce_on_startup": _to_bool(root.findtext("./bot/announce_on_startup"), True),
        "poll_seconds": _to_int(root.findtext("./bot/poll_seconds"), 20),
    }

    services: list[dict[str, Any]] = []
    for s in root.findall("./services/service"):
        services.append(
            {
                "key": (s.get("key") or "").strip(),
                "command": (s.findtext("command") or "").strip(),
                "label": (s.findtext("label") or "").strip(),
                "url_file": (s.findtext("url_file") or "").strip(),
                "tunnel_log_file": (s.findtext("tunnel_log_file") or "").strip(),
            }
        )

    channels: list[dict[str, Any]] = []
    for ch in root.findall("./channels/channel"):
        channel_id = _to_int(ch.get("id"), 0)
        modules = []
        for m in ch.findall("./module"):
            modules.append({"name": (m.get("name") or "").strip(), "settings": {}})
        if channel_id > 0:
            channels.append({"id": channel_id, "modules": modules})

    return {"bot": bot, "services": services, "channels": channels}


def load_router_config(config_file: str) -> dict[str, Any]:
    path = Path(config_file)
    if not path.exists():
        return {}

    suffix = path.suffix.lower()
    if suffix == ".json":
        return _load_json(path)
    if suffix == ".ini":
        return _load_ini(path)
    if suffix == ".xml":
        return _load_xml(path)
    raise RuntimeError(f"Unsupported config format: {suffix}. Use .json/.ini/.xml")

