#!/usr/bin/env bash
out=$(./docopt.py "$@" <<<'
Naval Fate.

Usage:
  naval_fate.py ship new <name>...
  naval_fate.py ship <name> move <x> <y> [--speed=<kn>] [-f...]
  naval_fate.py ship shoot <x> <y>
  naval_fate.py up...
  naval_fate.py do ARGS...
  naval_fate.py mine (set|remove) <x> <y> [--moored|--drifting]
  naval_fate.py -h | --help
  naval_fate.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Moored (anchored) mine.
  --drifting    Drifting mine.
')
printf "%s\n-----\n" "$out"
# x=0
# while read -r line; do
#   printf "%d: %s\n" "$x" "$line"
#   ((x++))
# done <<<"$out"

eval "$out"
