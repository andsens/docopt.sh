#!/usr/bin/env bash

required() {
  local initial_left=("${left[@]}")
  local pattern
  local unset_test_match=true
  $test_match && unset_test_match=false
  test_match=true
  for pattern in "$@"; do
    if ! $pattern; then
      left=("${initial_left[@]}")
      $unset_test_match && test_match=false
      return 1
    fi
  done
  if $unset_test_match; then
    test_match=false
    left=("${initial_left[@]}")
    for pattern in "$@"; do $pattern; done
  fi
  return 0
}
