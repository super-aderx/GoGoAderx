---
name: python
description: Python services, libraries and scripts (pytest, ruff, mypy or pyright; uv, poetry or pip)
---

# Profile: Python

## Detect
Applies when the repo, or a sub-directory of it, contains `pyproject.toml`, `requirements*.txt`, `setup.cfg`, `setup.py` or `Pipfile`. The area's `root` is the directory holding that file.

- **Runner prefix** from lockfiles: `uv.lock` → `uv run `; `poetry.lock` → `poetry run `; `Pipfile.lock` → `pipenv run `; otherwise no prefix (respect an existing `.venv/`).
- **test:** `pytest` if it appears in dependencies, `[tool.pytest.*]`, `pytest.ini` or `tox.ini`; otherwise `python -m unittest` when tests use `unittest`.
- **lint:** `ruff check .` if ruff is a dependency or `[tool.ruff]` exists; otherwise flake8 or pylint if configured. Omit if none.
- **typecheck:** `mypy .` if `[tool.mypy]`, `mypy.ini` or a mypy dependency exists; `pyright` if `pyrightconfig.json` or `[tool.pyright]` exists. Omit if neither.
- **format:** `ruff format {file}` if ruff is used; otherwise `black {file}`. Omit if none.
- **extensions:** `[".py"]`

## Area defaults

```json
{
  "profile": "python",
  "root": ".",
  "extensions": [".py"],
  "test": "pytest",
  "lint": "ruff check .",
  "typecheck": "mypy .",
  "format": "ruff format {file}"
}
```

Add the runner prefix to every command, and drop the keys for tools the project does not use.

## Where to look
- HTTP layer: FastAPI routers, Django `urls.py` and views, Flask blueprints; serializers and schemas (Pydantic, DRF).
- Domain and service layers, models (SQLAlchemy or Django ORM), and migrations (Alembic, `migrations/`).
- Settings and configuration modules, dependency injection wiring, middleware.
- Background work (Celery, RQ, scheduled jobs) and CLI entry points (`[project.scripts]`, `manage.py`, `__main__.py`).
- `conftest.py` files for shared fixtures and factories.

## Testing conventions
- Use plain `assert`, fixtures from `conftest.py` rather than setup methods, and `pytest.mark.parametrize` for tables of cases.
- Mirror the source tree under `tests/` and reuse existing fixtures and factories before writing new ones.
- Name tests after behavior (`test_rejects_expired_token`), not after functions.
- Mock at system boundaries (network, clock, third-party services), not internals. Follow whatever the repo already does for database access (real test database or transactional fixtures).
- API code: use the framework's test client. Async code: use the async plugin the repo already uses.
- Cover the failure paths: validation errors, permission denials, not-found.

## Build notes
- Match the existing typing level; annotate public function signatures.
- Migrations: generate them with the framework tool, keep them reversible, and keep schema changes and heavy backfills in separate steps.
- Avoid a bare `except:` or a broad `except Exception:` unless it re-raises or logs at a real boundary.
- Read configuration through the project's settings mechanism rather than `os.environ` in the middle of business logic.

## Dependency manifests
- Declared in `pyproject.toml` (`[project.dependencies]`, `[project.optional-dependencies]`, `[dependency-groups]`, or `[tool.poetry.dependencies]`), `requirements*.txt`, `setup.cfg` or `setup.py`, `Pipfile`.
- Lockfiles: `uv.lock`, `poetry.lock`, `Pipfile.lock`, or pinned `requirements*.txt`.
- Add dependencies with the project's tool (`uv add`, `poetry add`, or by editing the requirements file) so the lockfile stays in sync; separate runtime from dev-only dependencies.

## Shortcuts to flag
`# type: ignore`, `# noqa`, `# pragma: no cover`, `@pytest.mark.skip`, `pytest.skip(`, `@pytest.mark.xfail`, `@unittest.skip`, `except Exception: pass`, commented-out `assert` lines, leftover `print(`, `breakpoint()` or `pdb`, and new `TODO` or `FIXME`.

## Review checklist
- Exceptions swallowed or caught too broadly; errors that lose the original cause.
- Mutable default arguments; module-level state shared across requests.
- Blocking calls inside async code; missing `await`.
- N+1 queries, missing indexes for new query patterns, unbounded queries without pagination.
- Transactions and partial failure: multi-step writes that can leave data half-updated.
- Validation gaps in Pydantic models or serializers; trusting client-supplied fields (mass assignment).
- Injection: raw SQL built from strings, shell commands from user input, unsafe deserialization (`pickle`, `yaml.load`).
- Migration safety: long table locks, non-reversible operations, backfills in the same migration as schema changes.
- Resource leaks: unclosed files, connections or sessions.
- Public functions missing type hints where the codebase normally has them.
