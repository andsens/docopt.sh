#!/usr/bin/env bash

version='0.1.5'

doc="Usage: echo_ship_name.sh ship new <name>...
"

docopt "$@"

if $_ship && $_new; then
  echo $__name_
fi
