#!/usr/bin/env bash

either() {
  local initial_left=("${left[@]}")
  # shellcheck disable=SC2154
  local reset_from=${#params_set[@]}
  local best_match
  local previous_best
  local pattern
  for pattern in "$@"; do
    if $pattern; then
      if [[ -z $previous_best || ${#left[@]} -lt $previous_best ]]; then
        best_match=$pattern
        previous_best=${#left[@]}
      fi
    fi
    left=("${initial_left[@]}")
    unset_params "${params_set[@]:$reset_from}"
  done
  if [[ -n $best_match ]]; then
    $best_match
    return 0
  fi
  left=("${initial_left[@]}")
  unset_params "${params_set[@]:$reset_from}"
  return 1
}
