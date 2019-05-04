#!/usr/bin/env bash

unset_params() {
  while [[ $# -gt 0 ]]; do
    unset $$1
    shift
  done
}

splice_left() {
  local pos=$1
  local _left=("${left[@]:0:$pos}")
  _left+=("${left[@]:((pos+1))}")
  left=("${_left[@]}")
}
