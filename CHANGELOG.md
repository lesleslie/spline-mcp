# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-08-21

### Added

- spline-mcp: Adopt apply_tool_profile() with SPLINE_TOOL_PROFILE
- spline: Bodai plugin conversion (manifest, mcp.json, slash commands)

### Fixed

- spline-mcp: Correct stale docstring in apply_spline_tool_profile
- spline-mcp: Ruff cleanup (F401, I001, SIM102, F841)
- spline-mcp: Untrack .pyscn/reports/ artifacts
- spline-mcp: Use async helper, not sync wrapper

### Internal

- Gitignore runtime artifacts + untrack user-authorized cache files (bodai cleanup 2026-08-17)
- gitignore: Untrack .pyscn/ (bodai 2026-08-20)
- spline-mcp: Add [tool.creosote] block for dep hygiene
- spline-mcp: Bootstrap [tool.crackerjack] section + uv sync upgrade
- spline-mcp: Gitignore .lycheecache (file, not just dir)
- spline-mcp: Gitignore .lycheecache + .hypothesis
- spline-mcp: Untrack .lycheecache + .hypothesis runtime artifacts

## [0.3.1] - 2026-08-17

### Documentation

- Add Documentation tool group, fill env-var table, fix architecture diagram

### Internal

- Untrack backup files (.backup, .backup.json, .bak)

## [0.3.0] - 2026-08-12

### Changed

- spline-mcp: Adopt OneiricMCPConfig + mcp-common convention

### Fixed

- Drop unused # type: ignore directives
- Include 'click' in MOUSE_DOWN event docstring

### Internal

- Adopt register_http_health_route from mcp-common
- Bump oneiric dep to >=0.16.0
- Restore LICENSE and normalize attribution

## [0.2.3] - 2026-06-20

### Testing

- Add comprehensive test coverage

### Internal

- Add mypy.ini and .cache for quality tooling
- Bump version to 0.2.1
- Bump version to 0.2.2
- gitignore: Add backup file patterns to silence checkpoint tool artifacts

## [0.2.2] - 2026-05-10

### Testing

- Add comprehensive test coverage
- Add unit tests for generators and integration tests

### Internal

- Bump version to 0.2.1

## [0.2.1] - 2026-02-25

### Testing

- Add comprehensive test coverage
- Add unit tests for generators and integration tests
