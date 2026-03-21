# Orion Backend

FastAPI application for the Orion platform. See repository root [README.md](../README.md).

## Local development

```bash
pip install -e ".[dev]"
cp ../.env.example ../.env
uvicorn app.main:app --reload
```

## Migrations

```bash
alembic upgrade head
```

## Tests

```bash
pytest
```
