#!/usr/bin/env bash

_option() {
  local i
  for i in "${!left[@]}"; do
    local l=${left[$i]}
    if [[ ${parsed_params[${left[$i]}]} == $1 ]]; then
      splice_left "$i"
      params_set+=("$2")
      if [[ $3 ]]; then
        eval "$(printf -- "%s+=(%q)" "$2" "${parsed_values[$l]}")"
      else
        eval "$(printf -- "%s=%q" "$2" "${parsed_values[$l]}")"
      fi
      return 0
    fi
  done
  return 1
}
