#!/bin/bash
# Vundle plugin manager — decided 2026-07-16, deploy fleet-wide (all 5
# machines; vim on pramen supports Vundle the same as nvim elsewhere).
set -e
if [ ! -d ~/.vim/bundle/Vundle.vim ]; then
  git clone -q https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
fi
if command -v nvim >/dev/null 2>&1; then
  nvim --headless +PluginInstall +qall 2>&1 || true
elif command -v vim >/dev/null 2>&1; then
  vim +PluginInstall +qall 2>&1 || true
fi
