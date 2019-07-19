#!/usr/bin/env bash

# DOC='
# Usage:
#   commented_doc.sh [options] ARG

# Options:
#   -o  An "option"
# '
DOC="
Usage:
  commented_doc.sh [options] ARG

Options:
  -o  An option
"
"DOCOPT PARAMS"
eval "$(docopt "$@")"

echo "$ARG"
