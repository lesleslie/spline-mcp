# Repository Guidelines

## Project Structure & Module Organization

- `spline_mcp/` contains the MCP server package, including scene management tools, API clients, and runtime-state helpers.
- `settings/` stores configuration defaults, and `tests/` should mirror the package structure for object, material, event, and state coverage.
- Keep ecosystem and operator guidance in root docs rather than local scripts.

## Build, Test, and Development Commands

- `uv sync --group dev` installs development dependencies.
- Use the documented local server commands for stdio or HTTP smoke tests.
- `uv run pytest` runs the test suite.
- `uv run ruff check spline_mcp tests` and `uv run ruff format spline_mcp tests` cover linting and formatting.

## Coding Style & Naming Conventions

- Use explicit type hints, validated scene payloads, and small tool handlers.
- Keep modules snake_case and public tool responses structured and predictable.

## Testing Guidelines

- Add tests for scene queries, state changes, and API error handling.
- Prefer mocked Spline responses over brittle live integration tests unless the case explicitly requires end-to-end verification.

## Commit & Pull Request Guidelines

- Use focused commits such as `fix(materials): preserve color normalization`.
- PRs should describe affected tools, commands run, and any runtime-state changes.

## Security & Configuration Tips

- Never commit tokens or workspace credentials.
- Validate object identifiers and external URLs strictly.
