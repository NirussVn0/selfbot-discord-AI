# Self Discord Bot

Scaffolding for a Discord self-bot that AI bot 

## Toolchain
- [uv](https://github.com/astral-sh/uv) for dependency and virtualenv management
- [Docker](https://www.docker.com/) for containerization
- [Python](https://www.python.org/) 3.12 (managed via uv and Docker)

## Quick Start (uv)
```bash
# create and sync the virtual environment
uv sync

# activate the environment and run tests
source .venv/bin/activate
pytest
```

## Environment Variables
Copy `.env.example` to `.env`

Configuration defaults live in `config/config.yaml` and are validated via `pydantic` models.

## Docker Workflow
```bash
# build the production image
docker compose build

# run the stack (bot + redis)
docker compose up
```

The bot container mounts `./config` read-only so configuration edits on the host are picked up on restart.

## Testing
```bash
uv run pytest
```
# selfbot-discord-AI
