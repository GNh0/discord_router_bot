from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.modules.public_url_resolver import PublicUrlResolver


@dataclass(frozen=True)
class ServiceTarget:
    key: str
    command: str
    label: str
    url_file: str
    tunnel_log_file: str


class ServiceUrlRegistry:
    def __init__(self, services: list[ServiceTarget]) -> None:
        self._services = services
        self._by_key = {s.key: s for s in services}
        self._by_command = {s.command: s for s in services}

    @property
    def services(self) -> list[ServiceTarget]:
        return list(self._services)

    def by_key(self, key: str) -> ServiceTarget | None:
        return self._by_key.get(key)

    def by_command(self, command: str) -> ServiceTarget | None:
        return self._by_command.get(command)

    def read_url(self, service: ServiceTarget) -> str:
        return PublicUrlResolver(service.url_file, service.tunnel_log_file).read()


def build_service_registry(items: list[dict]) -> ServiceUrlRegistry:
    services: list[ServiceTarget] = []
    for item in items or []:
        key = str(item.get("key", "")).strip().lower()
        command = str(item.get("command", "")).strip().lower()
        label = str(item.get("label", "")).strip() or key
        url_file = str(item.get("url_file", "")).strip()
        tunnel_log_file = str(item.get("tunnel_log_file", "")).strip()
        if not (key and command and url_file and tunnel_log_file):
            continue
        services.append(
            ServiceTarget(
                key=key,
                command=command,
                label=label,
                url_file=url_file,
                tunnel_log_file=tunnel_log_file,
            )
        )
    return ServiceUrlRegistry(services)


def load_service_registry(services_file: str) -> ServiceUrlRegistry:
    path = Path(services_file)
    if not path.exists():
        return ServiceUrlRegistry([])
    raw = path.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    items = data.get("services", [])
    return build_service_registry(items)
