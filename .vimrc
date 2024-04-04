set nocompatible

colorscheme iceberg

set background=dark
set t_Co=256

filetype indent plugin on

syntax on

set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

Plugin 'chriskempson/base16-vim'
Plugin 'cocopon/iceberg.vim'

call vundle#end()
filetype plugin indent on

set number
set relativenumber
