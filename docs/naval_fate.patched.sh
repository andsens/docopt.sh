#!/usr/bin/env bash

DOC="Naval Fate.
Usage:
  naval_fate.sh <name> move <x> <y> [--speed=<kn>]
  naval_fate.sh shoot <x> <y>

Options:
  --speed=<kn>  Speed in knots [default: 10]."
# docopt parser below, refresh this parser with `docopt.sh naval_fate.patched.sh`
# shellcheck disable=2016,1075
docopt() { parse() { if ${DOCOPT_DOC_CHECK:-true}; then local doc_hash;if \
doc_hash=$(printf "%s" "$DOC" | (sha256sum 2>/dev/null || shasum -a 256)); then
if [[ ${doc_hash:0:5} != "$digest" ]]; then stderr "The current usage doc \
(${doc_hash:0:5}) does not match what the parser was generated with (${digest})
Run \`docopt.sh\` to refresh the parser.";_return 70;fi;fi;fi;local root_idx=$1
shift;argv=("$@");parsed=();left=();testdepth=0;local arg i o;while [[ \
${#argv[@]} -gt 0 ]]; do if [[ ${argv[0]} = "--" ]]; then for arg in \
"${argv[@]}"; do parsed+=("a:$arg");done;break;elif [[ ${argv[0]} = --* ]]; then
local long=${argv[0]%%=*};local similar=() match=false;i=0;for o in \
"${options[@]}"; do if [[ $o = *" $long "? ]]; then similar+=("$long");match=$i
break;fi;: $((i++));done;if [[ $match = false ]]; then i=0;for o in \
"${options[@]}"; do if [[ $o = *" $long"*? ]]; then local long_match=${o#* }
similar+=("${long_match% *}");match=$i;fi;: $((i++));done;fi;if [[ \
${#similar[@]} -gt 1 ]]; then error "${long} is not a unique prefix: \
${similar[*]}?";elif [[ ${#similar[@]} -lt 1 ]]; then if \
${DOCOPT_ADD_HELP:-true} && [[ $long = "--help" ]]; then stdout "$trimmed_doc"
_return 0;elif [[ ${DOCOPT_PROGRAM_VERSION:-false} != 'false' && $long = \
"--version" ]]; then stdout "$DOCOPT_PROGRAM_VERSION";_return 0;else error;fi
else if [[ ${options[$match]} = *0 ]]; then if [[ ${argv[0]} = *=* ]]; then
local long_match=${o#* };error "${long_match% *} must not have an argument";else
parsed+=("$match:true");argv=("${argv[@]:1}");fi;else if [[ ${argv[0]} = *=* \
]]; then parsed+=("$match:${argv[0]#*=}");argv=("${argv[@]:1}");else if [[ \
${#argv[@]} -le 1 || ${argv[1]} = '--' ]]; then error "${long} requires \
argument";fi;parsed+=("$match:${argv[1]}");argv=("${argv[@]:2}");fi;fi;fi;elif \
[[ ${argv[0]} = -* && ${argv[0]} != "-" ]]; then local remaining=${argv[0]#-}
while [[ -n $remaining ]]; do local short="-${remaining:0:1}" matched=false
remaining="${remaining:1}";i=0;for o in "${options[@]}"; do if [[ $o = "$short \
"* ]]; then if [[ $o = *0 ]]; then parsed+=("$i:true");else if [[ $remaining = \
'' ]]; then if [[ ${#argv[@]} -le 1 || ${argv[1]} = '--' ]]; then error \
"${short} requires argument";fi;parsed+=("$i:${argv[1]}");argv=("${argv[@]:1}")
else parsed+=("$i:$remaining");remaining='';fi;fi;matched=true;break;fi;: \
$((i++));done;if ! $matched; then if ${DOCOPT_ADD_HELP:-true} && [[ $short = \
"-h" ]]; then stdout "$trimmed_doc";_return 0;else error;fi;fi
argv=("${argv[@]:1}");done;elif ${DOCOPT_OPTIONS_FIRST:-false}; then for arg \
in "${argv[@]}"; do parsed+=("a:$arg");done;break;else parsed+=("a:${argv[0]}")
argv=("${argv[@]:1}");fi;done;i=0;while [[ $i -lt ${#parsed[@]} ]]; do
left+=("$i");: $((i++));done;if ! "node_$root_idx" || [ ${#left[@]} -gt 0 ]; \
then error;fi;return 0;};sequence() { local initial_left=("${left[@]}") node_idx
: $((testdepth++));for node_idx in "$@"; do if ! "node_$node_idx"; then
left=("${initial_left[@]}");: $((testdepth--));return 1;fi;done;if [[ \
$((--testdepth)) -eq 0 ]]; then left=("${initial_left[@]}");for node_idx in \
"$@"; do "node_$node_idx";done;fi;return 0;};choice() { local \
initial_left=("${left[@]}") best_match_idx match_count node_idx;: \
$((testdepth++));for node_idx in "$@"; do if "node_$node_idx"; then if [[ -z \
$match_count || ${#left[@]} -lt $match_count ]]; then best_match_idx=$node_idx
match_count=${#left[@]};fi;fi;left=("${initial_left[@]}");done;if [[ -n \
$best_match_idx ]]; then if [[ $((--testdepth)) -eq 0 ]]; then
"node_$best_match_idx";fi;return 0;fi;left=("${initial_left[@]}");return 1;}
optional() { local node_idx;for node_idx in "$@"; do "node_$node_idx";done
return 0;};switch() { local i;for i in "${!left[@]}"; do local l=${left[$i]}
if [[ ${parsed[$l]} = "$2" || ${parsed[$l]} = "$2":* ]]; then
left=("${left[@]:0:$i}" "${left[@]:((i+1))}");[[ $testdepth -gt 0 ]] && return 0
if [[ $3 = true ]]; then eval "((var_$1++))" || true;else eval "var_$1=true";fi
return 0;elif [[ ${parsed[$l]} = a:* && $2 = a:* ]]; then return 1;fi;done
return 1;};value() { local i;for i in "${!left[@]}"; do local l=${left[$i]};if \
[[ ${parsed[$l]} = "$2":* ]]; then left=("${left[@]:0:$i}" "${left[@]:((i+1))}")
[[ $testdepth -gt 0 ]] && return 0;local value;value=$(printf -- "%q" \
"${parsed[$l]#*:}");if [[ $3 = true ]]; then eval "var_$1+=($value)";else eval \
"var_$1=$value";fi;return 0;fi;done;return 1;};stdout() { printf -- "cat \
<<'EOM'\n%s\nEOM\n" "$1";};stderr() { printf -- "cat <<'EOM' >&2\n%s\nEOM\n" \
"$1";};error() { [[ -n $1 ]] && stderr "$1";stderr "$usage";_return 1;}
_return() { printf -- "exit %d\n" "$1";exit "$1";};set -e
trimmed_doc=${DOC:0:155};usage=${DOC:12:87};digest=3873e;options=(' --speed 1')
node_0(){ value __speed 0;};node_1(){ value _name_ a;};node_2(){ value _x_ a;}
node_3(){ value _y_ a;};node_4(){ switch move a:move;};node_5(){ switch shoot \
a:shoot;};node_6(){ optional 0;};node_7(){ sequence 1 4 2 3 6;};node_8(){
sequence 5 2 3;};node_9(){ choice 7 8;};cat <<<' docopt_exit() { [[ -n $1 ]] \
&& printf "%s\n" "$1" >&2;printf "%s\n" "${DOC:12:87}" >&2;exit 1;}';unset \
var___speed var__name_ var__x_ var__y_ var_move var_shoot;parse 9 "$@";local \
p=${DOCOPT_PREFIX:-''};unset "${p}__speed" "${p}_name_" "${p}_x_" "${p}_y_" \
"${p}move" "${p}shoot";eval "$p"'__speed=${var___speed:-10}';eval \
"$p"'_name_=${var__name_:-}';eval "$p"'_x_=${var__x_:-}';eval \
"$p"'_y_=${var__y_:-}';eval "$p"'move=${var_move:-false}';eval \
"$p"'shoot=${var_shoot:-false}';local docopt_i=1;[[ $BASH_VERSION =~ ^4.3 ]] \
&& docopt_i=2;for ((;docopt_i>0;docopt_i--)); do declare -p "${p}__speed" \
"${p}_name_" "${p}_x_" "${p}_y_" "${p}move" "${p}shoot";done;}
# docopt parser above, complete command for generating this parser is `docopt.sh naval_fate.patched.sh`

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
