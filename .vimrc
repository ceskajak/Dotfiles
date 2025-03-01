set nocompatible
set termguicolors

" set colorscheme
colorscheme catppuccin_frappe

" set transparent background
autocmd vimenter * hi Normal guibg=NONE ctermbg=NONE

filetype indent plugin on

syntax on

set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

Plugin 'chriskempson/base16-vim'

call vundle#end()
filetype plugin indent on

set number
set relativenumber
