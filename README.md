# yotg-media-bot

🎧 Multi-source media downloader for Telegram. Supports YouTube, Instagram, and more.

[![LICENSE](https://img.shields.io/github/license/mxpanf/yotg-media-bot?logo=opensourceinitiative&logoColor=white)](./LICENSE)
![CI](https://github.com/mxpanf/yotg-media-bot/actions/workflows/ci.yml/badge.svg)

## Setup

1. [Install `uv`](https://docs.astral.sh/uv/getting-started/installation/) (recommended package manager for this repo).
2. Sync dependencies once per checkout:

   ```bash
   uv sync
   ```

## Run the bot

Provide configuration (either `config/settings.yaml` or environment variables such as `YOTG_BOT_TOKEN`) and launch:

```bash
uv run python -m app.main
```

## Run tests

Execute the full pytest suite in an isolated environment:

```bash
uv run pytest
```

## Run linter

Lint Python sources with Ruff (and optionally add `uv run mypy` for type checks):

```bash
uv run ruff check
```
