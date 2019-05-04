#!/usr/bin/env bash

_switches() {
  local i
  for i in "${!left[@]}"; do
    if [[ ${parsed_params[${left[$i]}]} == $1 ]]; then
      splice_left "$i"
      params_set+=("$2")
      eval "$(printf -- "((%s++))" "$2")"
      return 0
    fi
  done
  return 1
}
