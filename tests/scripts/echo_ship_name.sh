#!/usr/bin/env bash

docopt_program_version='0.1.5'

doc="Usage: echo_ship_name.sh ship new <name>...
"
"DOCOPT PARAMS"
docopt "$@"

if $ship && $new; then
  echo $_name_
fi
