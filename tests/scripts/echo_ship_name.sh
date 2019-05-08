#!/usr/bin/env bash

version='0.1.5'

doc="Usage: echo_ship_name.sh ship new <name>...
"

docopt "$@"

if $ship && $new; then
  echo $_name_
fi
