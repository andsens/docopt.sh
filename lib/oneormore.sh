#!/usr/bin/env bash

oneormore() {
  local initial_left=("${left[@]}")
  # shellcheck disable=SC2154
  local reset_to=${#params_set[@]}
  local times=0
  local previous_left=${#initial_left[@]}
  while $1; do
    ((times++))
    if [[ $previous_left -eq ${#left[@]} ]]; then
      # This entire $previous_left thing doesn't make sense.
      # I couldn't find a case anywhere, where we would match something
      # but not remove something from $left.
      break
    fi
    previous_left=${#left[@]}
  done
  if [[ $times -ge 1 ]]; then
    return 0
  fi
  left=("${initial_left[@]}")
  unset_params "${params_set[@]:$reset_to}"
  return 1
}
