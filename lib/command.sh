#!/usr/bin/env bash

_command() {
  for l in "${left[@]}"; do
    if [[ ${parsed_params[$l]} == 'a' ]]; then
      if [[ ${parsed_values[$l]} == $1 ]]; then
        eval "$(printf -- "%s=true" "$2")"
        return 0
      else
        return 1
      fi
    fi
  done
  return 1
}
