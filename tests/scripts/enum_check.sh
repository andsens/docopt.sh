#!/usr/bin/env bash

DOC="Usage: enum_check.sh [options]

Options:
  --color=auto|always|never  Wether to use colors in output [default: auto]
"
"DOCOPT PARAMS"
docopt "$@"

if [[ ! $__color =~ ^auto|always|never$ ]]; then
  docopt_error "--color must be auto, always, or never"
fi

if [[ $__color = "always" || $__color = "auto" && -t 1 ]]; then
  enable_color=true
else
  enable_color=false
fi

if $enable_color; then
  echo -e "\e[1;32mHello!\e[0m"
else
  echo "Hello"
fi
