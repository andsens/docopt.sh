#!/usr/bin/env bash

DOCOPT_PROGRAM_VERSION='0.1.5'

DOC="Usage: echo_ship_name.sh ship new <name>...
"
"DOCOPT PARAMS"
docopt "$@"

if $ship && $new; then
  echo $_name_
fi
