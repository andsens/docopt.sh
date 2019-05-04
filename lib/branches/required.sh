#!/usr/bin/env bash

required() {
  local initial_left=("${left[@]}")
  # shellcheck disable=SC2154
  local reset_from=${#params_set[@]}
  local pattern
  for pattern in "$@"; do
    if ! $pattern; then
      left=("${initial_left[@]}")
      unset_params "${params_set[@]:$reset_from}"
      return 1
    fi
  done
  return 0
}
