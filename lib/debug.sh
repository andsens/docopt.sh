#!/usr/bin/env bash

print_left() {
  local old_x=${-//[^x]/}
  set +x
  $debug && printf -- "left (%d): " "${#left[@]}"
  $debug && printf -- "'%s' " "${left[@]}"
  $debug && printf -- "\n"
  [[ -n "$old_x" ]] && set -x
  return 0
}

debug() {
  $debug && printf -- "%s " "$@"
  return 0
}
