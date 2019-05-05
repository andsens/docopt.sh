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
  $bashprint && set -x
  if ! root; then
    return 1
  fi
  set +x
  type defaults 2>/dev/null && defaults
  if [[ ${#left[@]} -gt 0 ]]; then
    return 1
  fi
  return 0
}
