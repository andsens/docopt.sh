#!/usr/bin/env bash

optional() {
  local pattern
  for pattern in "$@"; do
    $pattern
  done
  return 0
}
