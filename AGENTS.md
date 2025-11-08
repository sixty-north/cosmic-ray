# Repository Guidelines

## Project Structure & Module Organization
Cosmic Ray uses a strict `src/` layout: core packages live in `src/cosmic_ray`, version metadata in `src/cosmic_ray/version.py`, and CLI surfaces under `src/cosmic_ray/cli`. Tests sit in `tests/unittests`, `tests/tools`, and `tests/e2e`, with shared fixtures in `tests/resources`. Documentation lives in `docs/source`, and helper utilities live in `tools/`. Mirror this hierarchy so new modules, tests, and assets stay discoverable.

## Build, Test, and Development Commands
- Cosmic Ray uses the uv project manager.
- `uv sync` installs the dependencies (include `--dev` automatically via `pyproject.toml` groups) and keeps `uv.lock` in sync.
- Always execute tooling through uv so the pinned virtual env is respected: `uv run pytest`, `uv run ruff check src tests`, `uv run cosmic-ray --help`.
- `uv run pytest` uses the defaults defined in `pyproject.toml`, including `tests` as the root and the e2e distributor/tester overrides.
- `uv run pytest --run-slow tests/e2e` exercises the long-running mutation workflows.
- `uv run ruff check src tests` (optionally `--fix`) keeps formatting and imports consistent.
- Docs build with `uv run sphinx-build -b html docs/source docs/_build/html`.

## Coding Style & Naming Conventions
Target idiomatic Python 3.9+ and PEP 8, but favor clarity when a rule conflicts with readability. `ruff` enforces a 120-character limit and `isort`-style grouping; let it rewrite imports instead of hand-tuning. Modules and packages stay snake_case, classes use CapWords, and CLI flags remain kebab-case (`cosmic-ray exec`). Keep shared configuration (`*.conf`, `pyproject.toml`) in the repo root or `tests/resources` so tooling can load them without extra paths.

## Testing Guidelines
Pytest backs every layer: unit coverage in `tests/unittests`, tool coverage in `tests/tools`, and slow integration runs in `tests/e2e`. Name files `test_<feature>.py`, keep test functions descriptive, and centralize fixtures in `tests/conftest.py` where possible. Tag long-lived scenarios with `@pytest.mark.slow` so contributors can include them via `--run-slow`. Add regression tests whenever you alter a mutation operator, CLI flag, or persistence layer.

## Commit & Pull Request Guidelines
Follow the format from `CONTRIBUTING.rst`: subjects are imperative and reference an issue (`Issue #1234 - Make operator ordering deterministic`) or start with `Doc -` for prose-only commits. Commit bodies should state problem, impact, and fix. Before opening a PR, run `git diff --check`, `ruff check`, and the relevant `pytest` targets; summarize those results plus reproduction steps (and screenshots/logs for reporting tools such as `cr-html`) in the PR description. Keep PRs focused and call out dependency or configuration changes in `pyproject.toml`.

## Security & Configuration Tips
Do not commit plaintext secrets—`deploy_key.enc` shows the expected encrypted form. Store experimental configs under `tests/resources` or ignore them locally. When developing HTTP distributors or remote workers, prefer the mocked services in `tests/tools` and document any new ports, certificates, or environment variables directly in the pull request.
