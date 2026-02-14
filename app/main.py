from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from app.discord_bot import RouterBot, load_channel_runtimes_from_data
from app.discord_bot.core import ChannelRuntime
from app.discord_bot.modules.url_router import UrlRouterModule
from app.modules import build_service_registry, load_router_config

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
CHANNEL_ID_RAW = os.getenv("DISCORD_CHANNEL_ID", "").strip()
TOKEN_FILE = os.getenv("TOKEN_FILE", "").strip()
DISCORD_CONFIG_FILE = os.getenv("DISCORD_CONFIG_FILE", "config/discord_router_config.json").strip()
SERVICES_FILE = os.getenv("DISCORD_SERVICES_FILE", "config/discord_services.json").strip()
ANNOUNCE_ON_STARTUP = os.getenv("DISCORD_ANNOUNCE_ON_STARTUP", "1").strip() == "1"
POLL_SECONDS = int(os.getenv("DISCORD_URL_POLL_SECONDS", "20"))


def resolve_token() -> str:
    if TOKEN:
        return TOKEN
    candidates: list[str] = []
    if TOKEN_FILE:
        candidates.append(TOKEN_FILE)
    candidates.extend(
        [
            "config/token.txt",
            r"D:\Coding\Python\Token.txt",
        ]
    )
    for c in candidates:
        path = Path(c)
        if not path.exists():
            continue
        try:
            token = path.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        if token:
            return token
    return ""


def fallback_runtime() -> list[ChannelRuntime]:
    if not CHANNEL_ID_RAW.isdigit():
        return []
    registry = build_service_registry(load_router_config(DISCORD_CONFIG_FILE).get("services", []))
    if not registry.services:
        # legacy fallback path
        registry = build_service_registry(load_router_config(SERVICES_FILE).get("services", []))
    return [
        ChannelRuntime(
            channel_id=int(CHANNEL_ID_RAW),
            modules=[
                UrlRouterModule(
                    services_file="",
                    announce_on_startup=ANNOUNCE_ON_STARTUP,
                    poll_seconds=max(5, POLL_SECONDS),
                    registry=registry,
                )
            ],
        )
    ]


def main() -> None:
    token = resolve_token()
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set")

    config_data = load_router_config(DISCORD_CONFIG_FILE)
    bot_cfg = dict(config_data.get("bot", {}) or {})
    announce = bool(bot_cfg.get("announce_on_startup", ANNOUNCE_ON_STARTUP))
    poll = max(5, int(bot_cfg.get("poll_seconds", POLL_SECONDS)))
    registry = build_service_registry(config_data.get("services", []))

    runtimes = load_channel_runtimes_from_data(
        config_data,
        default_registry=registry,
        default_announce_on_startup=announce,
        default_poll_seconds=poll,
    )

    if not runtimes:
        runtimes = fallback_runtime()
    if not runtimes:
        raise RuntimeError("No channel runtime configured. Set DISCORD_CONFIG_FILE or DISCORD_CHANNEL_ID.")

    bot = RouterBot(runtimes=runtimes)
    bot.run(token)


if __name__ == "__main__":
    main()
