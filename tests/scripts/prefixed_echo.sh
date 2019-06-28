#!/usr/bin/env bash

DOC="Usage: echo_ship_name.sh ship new <name>...
"
"DOCOPT PARAMS"
eval "$(docopt "$@")"

if $prefix_ship && $prefix_new; then
  echo $prefix__name_
fi
