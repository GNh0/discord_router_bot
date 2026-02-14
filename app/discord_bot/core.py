from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import discord
from discord.ext import commands

from app.discord_bot.modules.url_router import UrlRouterModule
from app.modules.service_url_registry import ServiceUrlRegistry


class DiscordModule:
    async def on_ready(self, bot: commands.Bot, channel_id: int) -> None:
        return None

    async def handle_command(
        self,
        bot: commands.Bot,
        message: discord.Message,
        command: str,
        args: str,
    ) -> bool:
        return False


@dataclass
class ChannelRuntime:
    channel_id: int
    modules: list[DiscordModule]


def _build_module(
    name: str,
    settings: dict[str, Any],
    default_registry: ServiceUrlRegistry,
    default_announce_on_startup: bool,
    default_poll_seconds: int,
) -> DiscordModule | None:
    if name == "url_router":
        return UrlRouterModule(
            services_file=str(settings.get("services_file", "")),
            announce_on_startup=bool(settings.get("announce_on_startup", default_announce_on_startup)),
            poll_seconds=max(5, int(settings.get("poll_seconds", default_poll_seconds))),
            registry=default_registry,
        )
    return None


def load_channel_runtimes_from_data(
    data: dict[str, Any],
    default_registry: ServiceUrlRegistry,
    default_announce_on_startup: bool,
    default_poll_seconds: int,
) -> list[ChannelRuntime]:
    items = data.get("channels", [])
    runtimes: list[ChannelRuntime] = []
    for item in items:
        try:
            channel_id = int(item.get("id", 0))
        except Exception:
            continue
        if channel_id <= 0:
            continue

        modules: list[DiscordModule] = []
        for m in item.get("modules", []):
            if isinstance(m, str):
                name = m
                settings: dict[str, Any] = {}
            elif isinstance(m, dict):
                name = str(m.get("name", "")).strip()
                settings = dict(m.get("settings", {}) or {})
            else:
                continue
            if not name:
                continue

            mod = _build_module(
                name,
                settings,
                default_registry=default_registry,
                default_announce_on_startup=default_announce_on_startup,
                default_poll_seconds=default_poll_seconds,
            )
            if mod is not None:
                modules.append(mod)

        if modules:
            runtimes.append(ChannelRuntime(channel_id=channel_id, modules=modules))
    return runtimes


class RouterBot(commands.Bot):
    def __init__(self, runtimes: list[ChannelRuntime]) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.runtimes = {rt.channel_id: rt for rt in runtimes}

    async def on_ready(self) -> None:
        print(f"discord bot logged in as {self.user}")
        for channel_id, runtime in self.runtimes.items():
            for module in runtime.modules:
                await module.on_ready(self, channel_id)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        runtime = self.runtimes.get(int(getattr(message.channel, "id", 0)))
        if runtime is None:
            return

        text = (message.content or "").strip()
        if not text.startswith("!"):
            return

        body = text[1:].strip()
        if not body:
            return

        if " " in body:
            command, args = body.split(" ", 1)
            args = args.strip()
        else:
            command, args = body, ""

        command = command.strip().lower()
        for module in runtime.modules:
            handled = await module.handle_command(self, message, command, args)
            if handled:
                return
