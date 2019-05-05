#!/usr/bin/env bash

_switch() {
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[$l]} == "$1" ]]; then
      splice_left "$i"
      $test_match && return 0
      if [[ $3 == true ]]; then
        eval "(($2++))"
      else
        eval "$2=true"
      fi
      return 0
    fi
  done
  return 1
}
