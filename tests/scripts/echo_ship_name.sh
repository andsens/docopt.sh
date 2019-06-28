#!/usr/bin/env bash

DOC="Usage: echo_ship_name.sh ship new <name>...
"
"DOCOPT PARAMS"
eval "$(docopt "$@")"

if $ship && $new; then
  echo $_name_
fi
