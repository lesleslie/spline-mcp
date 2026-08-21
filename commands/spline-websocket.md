---
description: Check the Spline Mahavishnu WebSocket connection, subscribe to a channel, and report integration status.
argument-hint: "[--channel <name>] [--status-only] [--duration <seconds>]"
allowed-tools: mcp__spline__get_websocket_status, mcp__spline__subscribe_to_channel, mcp__spline__get_integration_status
---

# /spline-websocket

Inspect and interact with the Spline Mahavishnu WebSocket bridge so generated Spline scenes can subscribe to runtime variable updates.

## Usage

`/spline-websocket [--channel <name>] [--status-only] [--duration <seconds>]`

Arguments:

- `--channel <name>`: optional channel to subscribe to after the status check. Defaults to `spline:variables`.
- `--status-only`: optional flag. Run only the status probe and skip the subscription.
- `--duration <seconds>`: optional subscription duration in seconds. After this period the subscription is closed and a summary of received messages is reported. Defaults to 30.

## Workflow

1. Call `mcp__spline__get_websocket_status` to confirm the WebSocket bridge is reachable and report the configured URL, reconnect policy, and any soft-failover state.
2. Call `mcp__spline__get_integration_status` for a rollup that includes both the WebSocket and (if configured) the n8n integration, so the user can see the full integration picture.
3. Unless `--status-only` was supplied, call `mcp__spline__subscribe_to_channel` with the requested channel and duration. Stream messages back to the user until the duration elapses, then summarize what was received.
4. If the status check returned `disconnected` or `error`, surface that to the user rather than silently retrying. Recommend the user verify `SPLINE_WEBSOCKET_URL` and the Mahavishnu server health.

## Example

`/spline-websocket --channel spline:variables --duration 60`
