#!/bin/bash

##############
# bare minimum
##############

# add VSCode repo
sudo rpm --import https://packages.microsoft.com/keys/microsoft.asc
echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" | sudo tee /etc/yum.repos.d/vscode.repo > /dev/null

# install the basics
sudo dnf install --assumeyes gvim zsh git lxappearance blueman nitrogen xinput acpi espeak slick-greeter code

# change shell to zsh
chsh -s /bin/zsh

# pull dotfiles from github
git clone https://github.com/ceskajak/Dotfiles.git

# link dotfiles
mkdir -p .config
mkdir -p .config/i3
mkdir -p .config/i3status
ln -sf Dotfiles/.vimrc .
ln -sf Dotfiles/.zshrc .
ln -sf Dotfiles/.tmux.conf .
ln -sf Dotfiles/i3.conf .config/i3/config
ln -sf Dotfiles/i3status.conf .config/i3status/i3status.conf

## if pavucontrol is white, check whether .config/gtk-4.0 exists

#######
# LaTeX
#######
sudo dnf install texlive latexmk texlive-chktex texlive-physics texlive-siunitx texlive-lipsum texlive-multirow

########
# THEMES
########
#TODO
# for lightdm-gtk-greeter copy into
# /usr/share/themes

################
# xfce4-terminal
################

git clone https://github.com/catppuccin/xfce4-terminal.git
mkdir -p ~/.local/share/xfce4
mkdir -p ~/.local/share/xfce4/terminal
mkdir -p ~/.local/share/xfce4/terminal/colorschemes
mv xfce4-terminal/themes/catppuccin-frappe.theme ~/.local/share/xfce4/terminal/colorschemes/
rm -rf xfce4-terminal
# Now remember to select the theme in the terminal config


#####
# vim
#####

# Vundle
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
vim +PluginInstall +qall

# catppuccin theme
git clone https://github.com/catppuccin/vim.git
mv vim/colors ~/.vim
rm -rf vim

###########
# oh-my-zsh
###########

# install oh-my-zsh
sh -c "$(wget https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)"

# plugins
mkdir -p $ZSH_CUSTOM/plugins

# zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
# catppuccin theme
git clone https://github.com/catppuccin/zsh-syntax-highlighting.git
mkdir -p ~/.zsh
mv zsh-syntax-highlighting/themes/catppuccin_frappe-zsh-syntax-highlighting ~/.zsh/
rm -rf zsh-syntax-highlighting

# fast-syntax-highlighting
git clone https://github.com/zdharma-continuum/fast-syntax-highlighting.git ${ZSH_CUSOM:-$HOME/.oh-my-zsh/custom}/plugins/fast-syntax-highlighting
# catppuccin theme
git clone https://github.com/catppuccin/zsh-fsh.git
mkdir -p ~/.config/fsh/
mv zsh-fsh/themes/catppuccin-frappe.ini ~/.config/fsh/
fast-theme XDG:catppuccin-frappe

######
# tmux
######

# TMP plugin manager
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm

#####
# git
#####
git config --global user.email "ceskajak@github.com"
git config --global user.name "Jakub Ceska"
git config --global core.editor "vim"
