#!/usr/bin/env bash

DOC="Naval Fate.
Usage:
  naval_fate.sh <name> move <x> <y> [--speed=<kn>]
  naval_fate.sh shoot <x> <y>

Options:
  --speed=<kn>  Speed in knots [default: 10]."
# docopt parser below, refresh this parser with `docopt.sh naval_fate.library.sh`
# shellcheck disable=2016,2086,2317,1090,1091,2034
docopt() { source "$(dirname "$0")/docopt-lib-0.9.17.sh" '0.0.0.dev0' || {
ret=$?;printf -- "exit %d\n" "$ret";exit "$ret";};set -e
trimmed_doc=${DOC:0:155};usage=${DOC:12:87};digest=3873e;options=(' --speed 1')
node_0(){ value __speed 0;};node_1(){ value _name_ a;};node_2(){ value _x_ a;}
node_3(){ value _y_ a;};node_4(){ switch move a:move;};node_5(){ switch shoot \
a:shoot;};node_6(){ sequence 1 4 2 3 7;};node_7(){ optional 0;};node_8(){
sequence 5 2 3;};node_9(){ choice 6 8;};cat <<<' docopt_exit() { [[ -n $1 ]] \
&& printf "%s\n" "$1" >&2;printf "%s\n" "${DOC:12:87}" >&2;exit 1;}';local \
varnames=(__speed _name_ _x_ _y_ move shoot) varname;for varname in \
"${varnames[@]}"; do unset "var_$varname";done;parse 9 "$@";local \
p=${DOCOPT_PREFIX:-''};for varname in "${varnames[@]}"; do unset "$p$varname"
done;eval $p'__speed=${var___speed:-10};'$p'_name_=${var__name_:-};'$p'_x_=${v'\
'ar__x_:-};'$p'_y_=${var__y_:-};'$p'move=${var_move:-false};'$p'shoot=${var_sh'\
'oot:-false};';local docopt_i=1;[[ $BASH_VERSION =~ ^4.3 ]] && docopt_i=2;for \
((;docopt_i>0;docopt_i--)); do for varname in "${varnames[@]}"; do declare -p \
"$p$varname";done;done;}
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
