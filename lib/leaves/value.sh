#!/usr/bin/env bash

# $1=variable name
# $2=is it a list?
# $3=option idx to find in the options list (or 'a' for 'argument')
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
