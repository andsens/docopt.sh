#!/usr/bin/env bash

_switch() {
  local i
  for i in "${!left[@]}"; do
    if [[ ${parsed_params[${left[$i]}]} == $1 ]]; then
      splice_left "$i"
      params_set+=("$2")
      if [[ $3 ]]; then
        eval "$(printf -- "((%s++))" "$2")"
      else
        eval "$(printf -- "%s=true" "$2")"
      fi
      return 0
    fi
  done
  return 1
}
