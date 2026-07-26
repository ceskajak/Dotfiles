#!/bin/bash
# tpm (tmux plugin manager) — fleet-wide, tmux is used on every machine.
# Was missing everywhere all session; .tmux.conf's tpm-init line was
# guarded to no-op without it. Installing closes that gap for real.
set -e
if [ ! -d ~/.tmux/plugins/tpm ]; then
  git clone -q https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi
if [ -n "$TMUX" ]; then
  ~/.tmux/plugins/tpm/bin/install_plugins || true
else
  tmux new-session -d -s __bootstrap 2>/dev/null || true
  tmux run-shell ~/.tmux/plugins/tpm/scripts/install_plugins.sh 2>&1 || true
  tmux kill-session -t __bootstrap 2>/dev/null || true
fi
