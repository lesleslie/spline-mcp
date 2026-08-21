---
description: Download a Spline scene into the local cache, validate it, and report cache stats (with optional cache cleanup).
argument-hint: <scene-url-or-id> [--no-validate] [--clear] [--stats-only]
allowed-tools: mcp__spline__download_scene, mcp__spline__validate_scene, mcp__spline__list_cached_scenes, mcp__spline__get_cache_stats, mcp__spline__clear_cache, mcp__spline__parse_scene_url
---

# /spline-assets

Manage Spline scene assets: download `.splinecode` payloads into the local cache, validate them, and inspect or clear the cache.

## Usage

`/spline-assets <scene-url-or-id> [--no-validate] [--clear] [--stats-only]`

Arguments:

- `<scene-url-or-id>`: full Spline export URL or bare scene ID. Used by the download and validate steps.
- `--no-validate`: optional flag. Skip the post-download validation step (not recommended for production use).
- `--clear`: optional flag. After reporting the result, call `mcp__spline__clear_cache` to wipe the local cache. Asks for confirmation before destructive action.
- `--stats-only`: optional flag. Skip the download entirely and just report the current cache contents and size.

## Workflow

1. If `--stats-only` is set: call `mcp__spline__get_cache_stats` followed by `mcp__spline__list_cached_scenes` and stop.
2. Otherwise call `mcp__spline__parse_scene_url` to resolve the input to a canonical scene ID.
3. Call `mcp__spline__download_scene` with the resolved URL to fetch and cache the `.splinecode` payload.
4. Unless `--no-validate` was supplied, call `mcp__spline__validate_scene` to confirm the cached file is a well-formed Spline payload.
5. Call `mcp__spline__get_cache_stats` to report the cache size before/after and `mcp__spline__list_cached_scenes` to confirm the new scene is present.
6. If `--clear` was supplied and the user confirmed destructive intent, call `mcp__spline__clear_cache` and report the new (empty) stats.

## Example

`/spline-assets https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode`
