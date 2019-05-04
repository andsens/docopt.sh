#!/usr/bin/env bash

_command() {
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} == 'a' ]]; then
      if [[ ${parsed_values[$l]} == "$1" ]]; then
        splice_left "$i"
        params_set+=("$2")
        if [[ $3 == true ]]; then
          eval "(($2++))"
        else
          eval "$2=true"
        fi
        return 0
      else
        return 1
      fi
    fi
  done
  return 1
}
