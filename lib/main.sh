#!/usr/bin/env bash

docopt() {
  parsed_params=()
  parsed_values=()
  argv=("$@")
  parse_argv
  left=()
  local i=0
  while [[ $i -lt ${#parsed_params[@]} ]]; do left+=("$i"); ((i++)); done
  params_set=()
  $debug && set -x
  root
  set +x
  defaults
  if [[ ${#left[@]} -gt 0 ]]; then
    return 1
  fi
}
