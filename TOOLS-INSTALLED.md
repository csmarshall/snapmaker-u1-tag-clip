# Tools installed

## altendky/onshape-mcp (planned, not yet run)

- **What:** Onshape MCP server for Claude Code, user scope, launched via `~/.local/bin/onshape-mcp-launch` (reads the OAuth client id/secret from the macOS Keychain).
- **Why:** model the U1 RFID tag holder in Onshape directly, with STEP/STL export and screenshots.
- **Installed by:** `./install_onshape_mcp.sh --apply`
- **Uninstall:**
  ```
  claude mcp remove --scope user onshape
  rm ~/.local/bin/onshape-mcp-launch
  security delete-generic-password -a "$USER" -s onshape-mcp-client-id
  security delete-generic-password -a "$USER" -s onshape-mcp-client-secret
  ```
  Then revoke the app in Onshape (My account > Applications) and delete the OAuth app in the dev portal.

## Ephemeral uv environments (nothing persistent installed)

- `uv run --with matplotlib --with numpy --with numpy-stl` was used to render STL previews (scratchpad render script). Cached by uv only; remove with `uv cache prune` if desired.
- The fixtures were built through the 3dp-mcp-server plugin's `create_model` (build123d). `u1/fixtures/u1_fixtures.py` reproduces them standalone with `uv run python u1/fixtures/u1_fixtures.py` (not yet run; the plugin output was verified instead).
