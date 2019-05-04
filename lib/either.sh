#!/usr/bin/env bash

either() {
  local initial_left=("${left[@]}")
  # shellcheck disable=SC2154
  local reset_to=${#params_set[@]}
  local best_match
  local previous_match
  for pattern in "$@"; do
    if $pattern; then
      if [[ -z $previous_match || $previous_match -gt ${#params_set[@]} ]]; then
        best_match=$pattern
      fi
    fi
    left=("${initial_left[@]}")
    unset_params "${params_set[@]:$reset_to}"
  done
  if [[ -n $best_match ]]; then
    $best_match
    return 0
  fi
  left=("${initial_left[@]}")
  unset_params "${params_set[@]:$reset_to}"
  return 1
}
