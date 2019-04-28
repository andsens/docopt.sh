#!/usr/bin/env bash

IFS=$\0 read -r
cmd_ship(){ cmd 'ship' }
cmd_new(){ cmd 'ship' }
arg_name(){ arg '<name>' }
oneormore_1() { arg_name }
req_1(){ all_of cmd_ship cmd_new oneormore_1 }
optional_1(){ option '--speed' }
req_2(){ all_of cmd_ship arg_name cmd_move arg_x arg_y optional_1 }
either_1(){ either req_1 req_2 }
docopt() { required either_1 }

required() {
  local left=(${p_left[@]})
  if [[ $p_collected == false ]]; then
      local collected=()
  else
      local collected=(${p_collected[@]})
  fi
  local l=(${left[@]})
  local c=(${collected[@]})
  local matched=true
  for pattern in "${@[@]}"; do
    p_left=(${l[@]})
    p_collected=(${c[@]})
    $pattern
    matched=$r_matched
    l=(${r_left[@]})
    c=(${r_collected[@]})
    if ! $r_matched; then
      r_matched=false
      r_left=(${left[@]})
      r_collected=(${collected[@]})
      return
      fi
  done
  r_matched=true
  r_left=(${l[@]})
  r_collected=(${c[@]})
  return
}
