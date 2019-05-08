#!/usr/bin/env bash

version='1.5.2'

doc="Naval Fate.

Usage:
  naval_fate.py ship new <name>...
  naval_fate.py ship <name> move <x> <y> [--speed=<kn>]
  naval_fate.py ship shoot <x> <y>
  naval_fate.py mine (set|remove) <x> <y> [--moored|--drifting]
  naval_fate.py -h | --help
  naval_fate.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Moored (anchored) mine.
  --drifting    Drifting mine.
"

docopt "$@"

if $ship == 'true' && $new == 'true'; then
  printf "Your new ship '%s' has been created.\n" "$_name_"
fi

if $ship == 'true' && $move == 'true'; then
  printf "The %s is now moving to %d,%d at %d knots.\n" "$_name_" "$_x_" "$_y_" "$__speed"
fi

if $ship == 'true' && $shoot == 'true'; then
  printf "You shoot at %d,%d. It's a hit!\n" "$_x_" "$_y_"
fi

if $mine == 'true' && $set == 'true'; then
  printf "A mine has been laid at %d,%d" "$_x_" "$_y_"
	if $__drifting; then
		printf " and is slowly drifting across the battlefield.\n"
	elif $__moored; then
		printf " and is anchored to that position.\n"
	else
		printf ".\n"
	fi
fi

if $mine == 'true' && $remove == 'true'; then
  printf "The mine at %d,%d has been removed.\n" "$_x_" "$_y_"
fi
