#!/usr/bin/env bash

docopt_extras() {
  local idx
  if [[ -z $docopt_help || $docopt_help != "false" ]]; then
    for idx in "${parsed_params[@]}"; do
      [[ $idx == 'a' ]] && continue
      if [[ ${options_short[$idx]} == "-h" || ${options_long[$idx]} == "--help" ]]; then
        docopt_help
        exit 0
      fi
    done
  fi
  if [[ -n $docopt_version ]]; then
    for idx in "${parsed_params[@]}"; do
      [[ $idx == 'a' ]] && continue
      if [[ ${options_long[$idx]} == "--version" ]]; then
        printf "%s\n" "$docopt_version"
        exit 0
      fi
    done
  fi
}
