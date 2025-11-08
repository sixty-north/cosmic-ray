# Repository Guidelines

## Project Structure & Module Organization
Cosmic Ray follows a `src/` layout: packages live in `src/cosmic_ray`, metadata in `src/cosmic_ray/version.py`, and CLI surfaces in `src/cosmic_ray/cli`. Tests live in `tests/unittests`, `tests/tools`, and `tests/e2e`, with fixtures/configs parked under `tests/resources`. Documentation resides in `docs/source`, and helper utilities live in `tools/`. The canonical upstream is `https://github.com/sixty-north/cosmic-ray`; match this layout when mirroring across forks.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` isolates dependencies before syncing/installing.
- `pip install -e .[dev]` (or `uv sync --dev`) installs the CLI plus dev tooling.
- `pytest` runs the default suite; `pytest --run-slow tests/e2e` adds the long mutation workflows.
- `ruff check src tests` (optionally `--fix`) keeps linting/ordering consistent.

## Coding Style & Naming Conventions
Target idiomatic Python 3.9+ and PEP 8, but favor clarity when a rule conflicts with readability. `ruff` enforces a 120-character limit and `isort`-style grouping; let it rewrite imports instead of hand-tuning. CI expects `uv ruff .` and `uv ruff format .` before every commit. Modules stay snake_case, classes use CapWords, and CLI flags remain kebab-case (`cosmic-ray exec`). Keep shared configuration (`*.conf`, `pyproject.toml`) in the repo root or `tests/resources` so tooling can load them without extra paths.

## Testing Guidelines
Pytest backs every layer: unit coverage in `tests/unittests`, tool coverage in `tests/tools`, and slow integration runs in `tests/e2e`. Name files `test_<feature>.py`, keep test functions descriptive, and centralize fixtures in `tests/conftest.py`. Tag long-lived scenarios with `@pytest.mark.slow` so contributors can opt in via `--run-slow`. Add regression tests whenever you alter a mutation operator, CLI flag, or persistence layer.

## Commit & Pull Request Guidelines
Follow the format from `CONTRIBUTING.rst`: subjects are imperative and reference an issue (`Issue #1234 - Make operator ordering deterministic`) or start with `Doc -` for prose-only commits. Commit bodies should state problem, impact, and fix. Before opening a PR, run `git diff --check`, `ruff check`, and the relevant `pytest` targets; summarize those results plus reproduction steps (and screenshots/logs for reporting tools such as `cr-html`) in the PR description. Keep PRs focused and call out dependency or configuration changes in `pyproject.toml`.

## Security & Configuration Tips
Do not commit plaintext secrets—`deploy_key.enc` shows the expected encrypted form. Store experimental configs under `tests/resources` or ignore them locally. When developing HTTP distributors or remote workers, prefer the mocked services in `tests/tools` and document any new ports, certificates, or environment variables directly in the pull request.
