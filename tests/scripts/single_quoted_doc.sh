#!/usr/bin/env bash

DOC='
Usage:
  single_quoted_doc.sh [options] ARG

Options:
  -o  An "option"
'
"DOCOPT PARAMS"
eval "$(docopt "$@")"

echo "$ARG"
