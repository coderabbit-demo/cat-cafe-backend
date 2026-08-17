# Cat Cafe Backend

FastAPI is the single source of truth for accounts, teas, availability, reservations, and external identity links. The Fresh and Slack clients only call this API.

## Run locally

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run:

```bash
cp .env.example .env
docker compose up -d db
uv sync --extra dev
uv run uvicorn app.main:app --reload --port 8444
```

Open `http://localhost:8444/docs`. The starter uses an in-memory service so it runs before PostgreSQL models are wired to repositories; `app/models/` and Alembic establish the production persistence boundary. Accounts, reservations, and sessions are cleared when the backend restarts.

## Development checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## API

- `POST /api/v1/auth/google`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /api/v1/teas`
- `GET /api/v1/availability?date=YYYY-MM-DD`
- CRUD under `/api/v1/reservations`
- Slack linking under `/api/v1/integrations/slack/users`
***
## Background: CodeRabbit demo use case

This repo models the smallest possible microservice architecture: one backend service (this repository) and one [frontend](https://github.com/coderabbit-demo/cat-cafe-frontend). Together they can be used to demonstrate both [automatic](https://docs.coderabbit.ai/knowledge-base/multi-repo-analysis#automatic-repository-linking) and [manual](https://docs.coderabbit.ai/knowledge-base/multi-repo-analysis#setting-it-up) repository linking.

PRs are scoped to a single repository, but shipping a feature or fix often requires carefully coordinated changes across several. Multi-repo analysis gives CodeRabbit visibility across that boundary, which organizations use to improve review comprehension, release velocity, and efficiency.

### To do

- [ ] Sign-in and authentication (so that reservations can work)
