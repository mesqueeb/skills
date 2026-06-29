#!/bin/sh
# install-from-local.sh — (re)install this repo's skills globally from this clone.
#
# Uses `skills add . -g -y --all`, which writes universal copies (so Codex et al.
# don't break) and symlinks for Claude Code, overwriting any existing global copies.
set -eu

cd "$(dirname "$0")"

echo "=== Installing skills from local clone ==="
skills add . -g -y --all

echo ""
echo "=== Done. Current global skills ==="
skills list -g
