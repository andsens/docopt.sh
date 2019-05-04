#!/usr/bin/env bash

either() {
  local initial_left=("${left[@]}")
  # shellcheck disable=SC2154
  local reset_from=${#params_set[@]}
  local best_match
  local previous_match
  local pattern
  for pattern in "$@"; do
    if $pattern; then
      if [[ -z $previous_match || $previous_match -gt ${#params_set[@]} ]]; then
        best_match=$pattern
      fi
    fi
    left=("${initial_left[@]}")
    unset_params "${params_set[@]:$reset_from}"
  done
  if [[ -n $best_match ]]; then
    printf "\n\n%s\n\n" "$best_match"
    $best_match
    return 0
  fi
  left=("${initial_left[@]}")
  unset_params "${params_set[@]:$reset_from}"
  return 1
}
