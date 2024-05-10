#!/usr/bin/env bash

DOC="μprog - A tiny program
Usage: uprog.sh [options]

Options:
  -d --do THINGTODO  Do the thing
"
"DOCOPT PARAMS"
eval "$(docopt "$@")"
