#!/usr/bin/env bash
# Quita cualquier atribución de Claude del mensaje de commit.
set -euo pipefail
msg_file="$1"
tmp="$(mktemp)"
grep -viE '^(co-authored-by:.*(claude|anthropic)|.*generated with \[?claude code)' "$msg_file" > "$tmp" || true
# Saca líneas en blanco sobrantes al final.
sed -e ':a' -e '/^\n*$/{$d;N;ba' -e '}' "$tmp" > "$msg_file"
rm -f "$tmp"
