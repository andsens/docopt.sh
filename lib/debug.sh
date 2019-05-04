#!/usr/bin/env bash

print_left() {
  local old_x=${-//[^x]/}
  set +x
  printf -- "left (%d): " "${#left[@]}"
  printf -- "'%s' " "${left[@]}"
  printf -- "\n"
  [[ -n "$old_x" ]] && set -x
}
