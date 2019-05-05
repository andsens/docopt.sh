#!/usr/bin/env bash

docopt() {
  for var in "${param_names[@]}"; do
    if declare -p "$var" &>/dev/null; then
      printf "Variable naming collision: %s\nUse a different prefix or rename your arguments." "$var"
      exit 1
    fi
  done
  parsed_params=()
  parsed_values=()
  argv=("$@")
  parse_argv
  docopt_extras
  left=()
  test_match=false
  local i=0
  while [[ $i -lt ${#parsed_params[@]} ]]; do left+=("$i"); ((i++)); done
  if ! root; then
    docopt_help
    exit 1
  fi
  type defaults &>/dev/null && defaults
  if [[ ${#left[@]} -gt 0 ]]; then
    docopt_help
    exit 1
  fi
  return 0
}
