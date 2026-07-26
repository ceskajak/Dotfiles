#!/bin/bash
# [[doctor]] project — pulls the latest fleet health report from pramen into
# the vault. Runs on ocean (workstation role only — it's the machine that
# owns the vault). Deliberately a PULL, not pramen pushing to ocean: ocean
# already has full SSH access to pramen and already owns the vault, so this
# needs zero new privilege anywhere. The alternative (pramen writing into
# ocean's home directory) would give the fleet's most security-sensitive
# machine write access it doesn't otherwise have. Decided 2026-07-26.
set -e

VAULT_TARGET="$HOME/Documents/Vault/Inventory/Doctor_Report.md"
TMPFILE="$(mktemp)"

if ! ssh -o ConnectTimeout=5 -o BatchMode=yes pramen "cat ~/doctor/reports/latest.md" > "$TMPFILE" 2>/dev/null; then
  echo "doctor-vault-sync: pramen unreachable or no report yet, leaving vault copy as-is" >&2
  rm -f "$TMPFILE"
  exit 0
fi

if [ ! -s "$TMPFILE" ]; then
  echo "doctor-vault-sync: got an empty report, leaving vault copy as-is" >&2
  rm -f "$TMPFILE"
  exit 0
fi

{
  echo "*Auto-synced from pramen (\`~/doctor/reports/latest.md\`) — don't hand-edit, changes will be overwritten on the next sync. See [[doctor]] for how this is generated.*"
  echo ""
  cat "$TMPFILE"
} > "$VAULT_TARGET"

rm -f "$TMPFILE"
echo "doctor-vault-sync: updated $VAULT_TARGET"
