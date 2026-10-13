#!/usr/bin/env bash
# Install altendky/onshape-mcp for Claude Code (user scope), secret kept in macOS Keychain.
# Default is a dry run that touches nothing; pass --apply to install.
unset TMOUT
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: install_onshape_mcp.sh [--apply] [--help]

  (no args)  dry run: check prerequisites and print what --apply would do
  --apply    store OAuth client id/secret in the macOS Keychain, write the
             launcher ~/.local/bin/onshape-mcp-launch, register the MCP at
             user scope, then run `onshape-mcp auth login`

Prerequisite: an Onshape OAuth app (https://dev-portal.onshape.com) with
redirect URL http://localhost:18338/callback. Have its client id and secret ready.

Uninstall: see TOOLS-INSTALLED.md.
EOF
}

APPLY=0
case "${1:-}" in
  "") ;;
  --apply) APPLY=1 ;;
  -h|--help) usage; exit 0 ;;
  *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
esac

# Pinned so the launcher cannot silently pull a newer (possibly compromised) release while it holds the OAuth secret.
# 0.5.2 was the npm latest on 2026-10-13 (sha512-xV+o48d4e1g9x4DbJbxLKBOfuL9brhsfdlOWlhzmuEzW9W0ctawfWIenJYrXa4mZQuqBq9gBjQxYuTROqzWoRA==). Review the changelog before bumping.
ONSHAPE_MCP_VERSION="0.5.2"
KC_ID_SVC="onshape-mcp-client-id"
KC_SECRET_SVC="onshape-mcp-client-secret"
LAUNCHER="$HOME/.local/bin/onshape-mcp-launch"

missing=0
for bin in claude npx security; do
  if command -v "$bin" >/dev/null 2>&1; then
    echo "ok:      $bin -> $(command -v "$bin")"
  else
    echo "MISSING: $bin" >&2
    missing=1
  fi
done
[ "$missing" -eq 0 ] || { echo "install the missing tools above and re-run" >&2; exit 3; }

if [ "$APPLY" -eq 0 ]; then
  cat <<EOF

DRY RUN, nothing changed. --apply would:
  1. prompt for the OAuth client id and secret, store both in Keychain
     (services: $KC_ID_SVC, $KC_SECRET_SVC)
  2. write $LAUNCHER (reads Keychain into ONSHAPE_MCP_AUTH__* env, execs npx onshape-mcp@$ONSHAPE_MCP_VERSION, pinned)
  3. claude mcp add --scope user onshape -- $LAUNCHER
  4. run the launcher's auth login (opens a browser for Onshape consent)
EOF
  exit 0
fi

read -r -p "Onshape OAuth client id: " CLIENT_ID
[ -n "$CLIENT_ID" ] || { echo "client id is empty" >&2; exit 4; }
# -w as the last option with no value makes `security` prompt for the secret without echoing it.
security add-generic-password -U -a "$USER" -s "$KC_ID_SVC" -w "$CLIENT_ID"
echo "Paste the OAuth client secret at the Keychain prompt:"
security add-generic-password -U -a "$USER" -s "$KC_SECRET_SVC" -w
unset CLIENT_ID

mkdir -p "$HOME/.local/bin"
cat >"$LAUNCHER" <<EOF
#!/usr/bin/env bash
# Launches onshape-mcp ${ONSHAPE_MCP_VERSION} with OAuth credentials read from the macOS Keychain.
unset TMOUT
set -euo pipefail
ONSHAPE_MCP_AUTH__CLIENT_ID="\$(security find-generic-password -a "\$USER" -s ${KC_ID_SVC} -w)"
ONSHAPE_MCP_AUTH__CLIENT_SECRET="\$(security find-generic-password -a "\$USER" -s ${KC_SECRET_SVC} -w)"
export ONSHAPE_MCP_AUTH__CLIENT_ID ONSHAPE_MCP_AUTH__CLIENT_SECRET
exec npx --yes onshape-mcp@${ONSHAPE_MCP_VERSION} "\$@"
EOF
chmod 0755 "$LAUNCHER"

claude mcp add --scope user onshape -- "$LAUNCHER"
"$LAUNCHER" auth login

echo
echo "Done. Restart Claude Code, then run /mcp and confirm 'onshape' is connected."
