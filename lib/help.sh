#!/usr/bin/env bash

docopt_help() {
  printf -- "%s" "{{doc}}"
}

docopt_error() {
  printf "%s\n" "$1"
  exit 1
}
