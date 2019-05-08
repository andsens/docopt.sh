#!/usr/bin/env bash

parse_argv() {
  while [[ ${#argv[@]} -gt 0 ]]; do
    if [[ ${argv[0]} == "--" ]]; then
      for arg in "${argv[@]}"; do
        parsed_params+=('a')
        parsed_values+=("$arg")
      done
      return
    elif [[ ${argv[0]} = --* ]]; then
      parse_long
    elif [[ ${argv[0]} == -* && ${argv[0]} != "-" ]]; then
      parse_shorts
    elif {{options_first}}; then
      for arg in "${argv[@]}"; do
        parsed_params+=('a')
        parsed_values+=("$arg")
      done
      return
    else
      parsed_params+=('a')
      parsed_values+=("${argv[0]}")
      argv=("${argv[@]:1}")
    fi
  done
}
