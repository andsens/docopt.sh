#!/usr/bin/env bash

# $1=variable name
# $2=is it a list?
# $3=option idx to find in the options list
_switch() {
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} == "$3" ]]; then
      left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
      $test_match && return 0
      if [[ $2 == true ]]; then
        eval "(($1++))"
      else
        eval "$1=true"
      fi
      return 0
    fi
  done
  return 1
}
