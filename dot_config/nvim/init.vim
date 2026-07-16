" ~/.config/nvim/init.vim — managed by chezmoi.
" Bridges nvim to the existing (chezmoi-managed) ~/.vimrc, per nvim's own
" documented vim-compatibility recipe (:help nvim-from-vim). Deliberately
" minimal: does not alter .vimrc content, colorscheme, or plugin decisions —
" those are separate, not-yet-decided items. See vault [[dotfiles]].
set runtimepath^=~/.vim runtimepath+=~/.vim/after
let &packpath = &runtimepath
source ~/.vimrc
