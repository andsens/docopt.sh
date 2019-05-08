#!/usr/bin/env bash

docopt_setup() {
  argv=("$@")
  options_short=({{options_short}})
  options_long=({{options_long}})
  options_argcount=({{options_argcount}})
  param_names=({{param_names}})
  parsed_params=()
  parsed_values=()
  left=()
  test_match=false
  docopt_options_first=${docopt_options_first:-false}
  docopt_help=${docopt_help:-true}
  for var in "${param_names[@]}"; do
    if declare -p "$var" &>/dev/null; then
      printf "Variable naming collision: %s\nUse a different prefix or rename your arguments." "$var"
      exit 1
    fi
  done
}
