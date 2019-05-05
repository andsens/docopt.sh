#!/usr/bin/env bash

docopt() {
  docopt_setup "$@"
  parse_argv
  docopt_extras
  local i=0
  while [[ $i -lt ${#parsed_params[@]} ]]; do left+=("$i"); ((i++)); done
  if ! {{root_fn}}; then
    docopt_help
    exit 1
  fi
  type docopt_defaults &>/dev/null && docopt_defaults
  if [[ ${#left[@]} -gt 0 ]]; then
    docopt_help
    exit 1
  fi
  docopt_teardown
  return 0
}
