#!/usr/bin/env bash

parse_shorts() {
  token=${argv[0]}
  argv=("${argv[@]:1}")
  [[ $token == -* && $token != --* ]] || assert_fail
  local left=${token#-}
  while [[ -n $left ]]; do
    short="-${left:0:1}"
    left="${left:1}"
    local i=0
    local similar=()
    local similar_idx=false
    for o in "${options_short[@]}"; do
      if [[ $o == "$short" ]]; then
        similar+=("$short")
        [[ $similar_idx == false ]] && similar_idx=$i
      fi
      ((i++))
    done
    if [[ ${#similar[@]} -gt 1 ]]; then
      die "%s is specified ambiguously %d times" "$short" "${#similar[@]}"
    elif [[ ${#similar[@]} -lt 1 ]]; then
      similar_idx=${#options_short[@]}
      value=true
      options_short+=("$short")
      options_long+=('')
      options_argcount+=(0)
    else
      value=false
      if [[ ${options_argcount[$similar_idx]} -ne 0 ]]; then
        if [[ $left == '' ]]; then
          if [[ ${#argv[@]} -eq 0 || ${argv[0]} == '--' ]]; then
            die "%s requires argument" "$short"
          fi
          value=${argv[0]}
          argv=("${argv[@]:1}")
        else
          value=$left
          left=''
        fi
      fi
      if [[ $value == false ]]; then
        value=true
      fi
    fi
    parsed_params+=("$similar_idx")
    parsed_values+=("$value")
  done
}
