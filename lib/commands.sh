#!/usr/bin/env bash

_commands() {
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} == 'a' ]]; then
      if [[ ${parsed_values[$l]} == "$1" ]]; then
        splice_left "$i"
        params_set+=("$2")
        eval "$(printf -- "((%s++))" "$2")"
        return 0
      else
        return 1
      fi
    fi
  done
  return 1
}
