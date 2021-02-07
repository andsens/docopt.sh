#!/usr/bin/env bash

DOC="Naval Fate.
Usage:
  naval_fate.sh <name> move <x> <y> [--speed=<kn>]
  naval_fate.sh shoot <x> <y>

Options:
  --speed=<kn>  Speed in knots [default: 10]."
# docopt parser below, refresh this parser with `docopt.sh naval_fate.library.sh`
# shellcheck disable=2016,1090,1091,2034
docopt() { source "$(dirname "$0")/docopt-lib-0.9.17.sh" '0.9.17' || { ret=$?
printf -- "exit %d\n" "$ret"; exit "$ret"; }; set -e; trimmed_doc=${DOC:0:155}
usage=${DOC:12:87}; digest=3873e; shorts=(''); longs=(--speed); argcounts=(1)
node_0(){ value __speed 0; }; node_1(){ value _name_ a; }; node_2(){ value _x_ a
}; node_3(){ value _y_ a; }; node_4(){ _command move; }; node_5(){
_command shoot; }; node_6(){ optional 0; }; node_7(){ required 1 4 2 3 6; }
node_8(){ required 5 2 3; }; node_9(){ either 7 8; }; node_10(){ required 9; }
cat <<<' docopt_exit() { [[ -n $1 ]] && printf "%s\n" "$1" >&2
printf "%s\n" "${DOC:12:87}" >&2; exit 1; }'; unset var___speed var__name_ \
var__x_ var__y_ var_move var_shoot; parse 10 "$@"
local prefix=${DOCOPT_PREFIX:-''}; unset "${prefix}__speed" "${prefix}_name_" \
"${prefix}_x_" "${prefix}_y_" "${prefix}move" "${prefix}shoot"
eval "${prefix}"'__speed=${var___speed:-10}'
eval "${prefix}"'_name_=${var__name_:-}'; eval "${prefix}"'_x_=${var__x_:-}'
eval "${prefix}"'_y_=${var__y_:-}'; eval "${prefix}"'move=${var_move:-false}'
eval "${prefix}"'shoot=${var_shoot:-false}'; local docopt_i=1
[[ $BASH_VERSION =~ ^4.3 ]] && docopt_i=2; for ((;docopt_i>0;docopt_i--)); do
declare -p "${prefix}__speed" "${prefix}_name_" "${prefix}_x_" "${prefix}_y_" \
"${prefix}move" "${prefix}shoot"; done; }
# docopt parser above, complete command for generating this parser is `docopt.sh --library='"$(dirname "$0")/docopt-lib-0.9.17.sh"' naval_fate.library.sh`

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
