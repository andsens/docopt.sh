#!/usr/bin/env bash

DOC="Naval Fate.
Usage:
  naval_fate.sh <name> move <x> <y> [--speed=<kn>]
  naval_fate.sh shoot <x> <y>

Options:
  --speed=<kn>  Speed in knots [default: 10]."

naval_fate() {
  eval "$(docopt "$@")"
  if $move; then
    printf "The %s is now moving to %d,%d at %d knots.\n" "$_name_" "$_x_" "$_y_" "$__speed"
  fi
  if $shoot; then
    printf "You shoot at %d,%d. It's a hit!\n" "$_x_" "$_y_"
  fi
  return 0
}
naval_fate "$@"
