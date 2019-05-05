#!/usr/bin/env bash

_argument() {
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} == 'a' ]]; then
      splice_left "$i"
      $test_match && return 0
      local value=$(printf -- "%q" "${parsed_values[$l]}")
      if [[ $3 == true ]]; then
        eval "$2+=($value)"
      else
        eval "$2=$value"
      fi
      return 0
    fi
  done
  return 1
}
