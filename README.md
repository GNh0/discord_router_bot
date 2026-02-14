# Discord Router Bot

독립 디스코드 봇 프로젝트입니다.

## 기능
- 채널별 모듈 attach 구조
- 서비스 URL 라우팅 (`!챗봇`, `!트레이딩`, `!weburl <service_key>`)
- URL 파일 + 터널 로그 기반 URL 감지

## 설치
```powershell
cd d:\Coding\Python\Stock\discord_router_bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

## 설정
- `DISCORD_CONFIG_FILE` 경로의 설정 파일 1개를 사용합니다.
- 지원 포맷: `.json`, `.ini`, `.xml`
- 기본 경로: `config/discord_router_config.json`
- 같은 내용의 예시 파일:
  - `config/discord_router_config.json`
  - `config/discord_router_config.ini`
  - `config/discord_router_config.xml`

## 실행
```powershell
python -m app.main
```
또는
```powershell
run_bot.bat
```

## 구조
- `app/main.py`: 엔트리포인트
- `app/discord_bot/core.py`: BotCore + 채널 런타임 로더
- `app/discord_bot/modules/url_router.py`: URL 라우터 모듈
- `app/modules/public_url_resolver.py`: URL 추출기
- `app/modules/service_url_registry.py`: 서비스 레지스트리
