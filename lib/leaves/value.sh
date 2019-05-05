#!/usr/bin/env bash

_value() {
  local i
  local needle=${3:-'a'}
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} == "$needle" ]]; then
      left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
      $test_match && return 0
      local value=$(printf -- "%q" "${parsed_values[$l]}")
      if [[ $2 == true ]]; then
        eval "$1+=($value)"
      else
        eval "$1=$value"
      fi
      return 0
    fi
  done
  return 1
}
