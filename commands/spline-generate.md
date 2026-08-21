---
description: Generate React/Next.js/Vanilla JS integration code from a Spline scene URL using the full-integration generator.
argument-hint: <scene-url-or-id> [--framework react|nextjs|vanilla] [--typescript] [--lazy-load] [--no-semicolons]
allowed-tools: mcp__spline__generate_full_integration, mcp__spline__parse_scene_url, mcp__spline__build_export_url, mcp__spline__validate_scene, mcp__spline__generate_snippet
---

# /spline-generate

Generate a complete Spline 3D scene integration (component code + variable bindings + event handlers + WebSocket hookup) from a Spline scene URL or scene ID.

## Usage

`/spline-generate <scene-url-or-id> [--framework react|nextjs|vanilla] [--typescript] [--lazy-load] [--no-semicolons]`

Arguments:

- `<scene-url-or-id>`: full Spline export URL (`https://prod.spline.design/<id>/scene.splinecode`) or a bare scene ID. The scene must have been previously downloaded by `mcp__spline__download_scene` and live in the cache.
- `--framework react|nextjs|vanilla`: optional target framework. Defaults to `react`.
- `--typescript`: optional flag. Emit TypeScript instead of plain JavaScript. Defaults to on for React/Next.js.
- `--lazy-load`: optional flag. Wrap the scene in `React.lazy` + `<Suspense>`. Defaults to on for React/Next.js.
- `--no-semicolons`: optional flag. Emit code without trailing semicolons.

## Workflow

1. Call `mcp__spline__parse_scene_url` on the input to extract the canonical scene ID (or accept it as-is if a bare ID was supplied).
2. Call `mcp__spline__build_export_url` to derive the export URL the server will use to fetch the cached scene.
3. Call `mcp__spline__validate_scene` on the resolved URL to confirm the `.splinecode` payload is well-formed before generation.
4. Call `mcp__spline__generate_full_integration` with the resolved URL and the chosen framework/options. This returns the full component, variable bindings, event handlers, and WebSocket hookup in one response.
5. If the user only wants a single snippet (e.g. just the runtime initialization block), call `mcp__spline__generate_snippet` instead of `generate_full_integration`.
6. Report the generated code and any next-step hints (e.g. which package to install, how to wire the WebSocket channel).

## Example

`/spline-generate https://prod.spline.design/6Wq1Q7YGyM-iab9i/scene.splinecode --framework react`
