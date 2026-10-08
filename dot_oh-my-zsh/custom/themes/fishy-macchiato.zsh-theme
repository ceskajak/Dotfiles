# fishy layout (oh-my-zsh) recoloured with fixed Catppuccin Macchiato hex
# colours, so the prompt looks the same in any terminal on any host.
# Terminals that don't advertise truecolor get the nearest 256 colours.
[[ $COLORTERM == (truecolor|24bit) ]] || zmodload zsh/nearcolor

_fishy_collapsed_wd() {
  local i pwd
  pwd=("${(s:/:)PWD/#$HOME/~}")
  if (( $#pwd > 1 )); then
    for i in {1..$(($#pwd-1))}; do
      if [[ "$pwd[$i]" = .* ]]; then
        pwd[$i]="${${pwd[$i]}[1,2]}"
      else
        pwd[$i]="${${pwd[$i]}[1]}"
      fi
    done
  fi
  echo "${(j:/:)pwd}"
}

local c_user='#f5bde6' c_host='#c6a0f6' c_path='#8aadf4' c_red='#ed8796'
[ $UID -eq 0 ] && c_user=$c_red
[ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ] && c_host='#eed49f'
PROMPT="%F{$c_user}%n%f@%F{$c_host}%m %F{$c_path}\$(_fishy_collapsed_wd)%f%(!.#.>) "
PROMPT2="%F{$c_red}\\ %f"

local return_status="%B%F{$c_red}%(?..%?)%f%b"
RPROMPT="${RPROMPT}"'${return_status}$(git_prompt_info)$(git_prompt_status)%f'

ZSH_THEME_GIT_PROMPT_PREFIX=" "
ZSH_THEME_GIT_PROMPT_SUFFIX=""
ZSH_THEME_GIT_PROMPT_DIRTY=""
ZSH_THEME_GIT_PROMPT_CLEAN=""

ZSH_THEME_GIT_PROMPT_ADDED="%B%F{#a6da95}+"
ZSH_THEME_GIT_PROMPT_MODIFIED="%B%F{#8aadf4}!"
ZSH_THEME_GIT_PROMPT_DELETED="%B%F{#ed8796}-"
ZSH_THEME_GIT_PROMPT_RENAMED="%B%F{#c6a0f6}>"
ZSH_THEME_GIT_PROMPT_UNMERGED="%B%F{#eed49f}#"
ZSH_THEME_GIT_PROMPT_UNTRACKED="%B%F{#8bd5ca}?"
