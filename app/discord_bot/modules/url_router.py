from __future__ import annotations

import asyncio

import discord
from discord.ext import commands

from app.modules.service_url_registry import ServiceTarget, ServiceUrlRegistry, load_service_registry


class UrlRouterModule:
    def __init__(
        self,
        services_file: str = "",
        announce_on_startup: bool = True,
        poll_seconds: int = 20,
        registry: ServiceUrlRegistry | None = None,
    ) -> None:
        self.services_file = services_file
        self.announce_on_startup = announce_on_startup
        self.poll_seconds = poll_seconds
        self.registry = registry if registry is not None else self._load_registry()
        self.last_urls: dict[str, str] = {}
        self._watch_started = False

    def _load_registry(self) -> ServiceUrlRegistry:
        try:
            return load_service_registry(self.services_file)
        except Exception as exc:
            print(f"url_router: failed to load services file '{self.services_file}': {exc}")
            return ServiceUrlRegistry([])

    async def on_ready(self, bot: commands.Bot, channel_id: int) -> None:
        if self.announce_on_startup:
            await self._announce_current_urls(bot, channel_id, wait_if_missing=True)
        if not self._watch_started:
            self._watch_started = True
            bot.loop.create_task(self._watch_url_changes(bot, channel_id))

    async def handle_command(
        self,
        bot: commands.Bot,
        message: discord.Message,
        command: str,
        args: str,
    ) -> bool:
        if not self.registry.services:
            await message.channel.send("URL 서비스 설정이 비어 있습니다.")
            return True

        if command == "weburl":
            key = args.strip().lower()
            if not key:
                listing = ", ".join(f"`!{s.command}`" for s in self.registry.services)
                await message.channel.send(f"사용 가능한 명령: {listing}")
                return True
            service = self.registry.by_key(key)
            if service is None:
                await message.channel.send(f"지원 서비스가 아닙니다: {key}")
                return True
            await self._reply_service_url(message.channel, service)
            return True

        service = self.registry.by_command(command)
        if service is None:
            return False
        await self._reply_service_url(message.channel, service)
        return True

    async def _reply_service_url(self, channel: discord.abc.Messageable, service: ServiceTarget) -> None:
        url = self.registry.read_url(service)
        if not url:
            await channel.send(f"{service.label} 외부 URL을 아직 찾지 못했습니다. 잠시 후 다시 시도하세요.")
            return
        self.last_urls[service.key] = url
        await channel.send(f"{service.label} 주소: {url}")

    async def _announce_current_urls(self, bot: commands.Bot, channel_id: int, wait_if_missing: bool) -> None:
        channel = bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            print(f"url_router: invalid channel_id={channel_id}")
            return

        for service in self.registry.services:
            timeout = 120 if wait_if_missing else 0
            elapsed = 0
            url = self.registry.read_url(service)
            while wait_if_missing and not url and elapsed < timeout:
                await asyncio.sleep(2)
                elapsed += 2
                url = self.registry.read_url(service)

            if not url:
                await channel.send(
                    f"{service.label} 외부 URL을 아직 찾지 못했습니다. "
                    f"`!{service.command}` 또는 `!weburl {service.key}`로 확인하세요."
                )
                continue

            self.last_urls[service.key] = url
            await channel.send(f"{service.label} 외부 웹 주소 준비 완료: {url}")

    async def _watch_url_changes(self, bot: commands.Bot, channel_id: int) -> None:
        await bot.wait_until_ready()
        channel = bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        while not bot.is_closed():
            await asyncio.sleep(max(5, self.poll_seconds))
            for service in self.registry.services:
                url = self.registry.read_url(service)
                if not url:
                    continue
                if self.last_urls.get(service.key) != url:
                    self.last_urls[service.key] = url
                    await channel.send(f"{service.label} 외부 웹 주소가 갱신되었습니다: {url}")
