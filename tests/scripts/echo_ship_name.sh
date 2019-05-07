#!/usr/bin/env bash

version='0.1.5'

doc="Usage:
  naval_fate.py ship new <name>...
"

docopt "$@"

if [[ $_ship && $_new ]]; then
  echo $__name_
fi
