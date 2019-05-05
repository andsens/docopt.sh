#!/usr/bin/env bash

splice_left() {
  local pos=$1
  local _left=("${left[@]:0:$pos}")
  _left+=("${left[@]:((pos+1))}")
  left=("${_left[@]}")
}
