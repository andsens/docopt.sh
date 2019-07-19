#!/usr/bin/env bash

DOC="
Usage:
  escaped_quotes_in_doc.sh [options]

Options:
  -v  Variable to test [default: \$foo]
  -s  Thing to test against, like \"hello\" [default: hi]
"
"DOCOPT PARAMS"
eval "$(docopt "$@")"

if [[ ${!_v} == "$_s" ]]; then
  echo 'equal'
  exit 0
else
  echo 'unequal'
  exit 1
fi
