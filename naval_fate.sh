#!/usr/bin/env bash

version='1.5.2'

doc="Naval Fate.

Usage:
  naval_fate.py ship new <name>...
  naval_fate.py ship <name> move <x> <y> [--speed=<kn>]
  naval_fate.py ship shoot <x> <y>
  naval_fate.py mine (set|remove) <x> <y> [--moored|--drifting]
  naval_fate.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --speed=<kn>  Speed in knots [default: 10].
  --moored      Moored (anchored) mine.
  --drifting    Drifting mine."
# docopt parser below, refresh this parser with `docopt.sh naval_fate.sh`
arg0() { _value __speed false 0; }; arg1() { _switch __moored false 1; }
arg2() { _switch __drifting false 2; }; arg3() { _switch __version false 3; }
opt4() { _value _name_ true ''; }; opt5() { _value _x_ false ''; }; opt6() {
_value _y_ false ''; }; cmd7() { _command ship false ship; }; cmd8() {
_command new false new; }; cmd9() { _command move false move; }; cmd10() {
_command shoot false shoot; }; cmd11() { _command mine false mine; }; cmd12() {
_command set false set; }; cmd13() { _command remove false remove; }
oneormore3() { oneormore opt4; }; req4() { required cmd7 cmd8 oneormore3; }
optional11() { optional arg0; }; req12() {
required cmd7 opt4 cmd9 opt5 opt6 optional11; }; req17() {
required cmd7 cmd10 opt5 opt6; }; either21() { either cmd12 cmd13; }; req22() {
required either21; }; either27() { either arg1 arg2; }; optional28() {
optional either27; }; req29() { required cmd11 req22 opt5 opt6 optional28; }
req31() { required arg3; }; either32() { either req4 req12 req17 req29 req31; }
root() { required either32; }; _command() { local i; for i in "${!left[@]}"; do
local l=${left[$i]}; if [[ ${parsed_params[$l]} == 'a' ]]; then
if [[ ${parsed_values[$l]} != "$3" ]]; then return 1; fi
left=("${left[@]:0:$i}" "${left[@]:((i+1))}"); $test_match && return 0
if [[ $2 == true ]]; then eval "(($1++))"; else eval "$1=true"; fi; return 0
fi; done; return 1; }; either() { local initial_left=("${left[@]}")
local best_match; local previous_best; local pattern
local unset_test_match=true; $test_match && unset_test_match=false
test_match=true; for pattern in "$@"; do if $pattern; then
if [[ -z $previous_best || ${#left[@]} -lt $previous_best ]]; then
best_match=$pattern; previous_best=${#left[@]}; fi; fi
left=("${initial_left[@]}"); done; $unset_test_match && test_match=false
if [[ -n $best_match ]]; then $best_match; return 0; fi
left=("${initial_left[@]}"); return 1; }; oneormore() { local times=0
# shellcheck disable=SC2154
local previous_left=${#left[@]}; while $1; do ((times++))
if [[ $previous_left -eq ${#left[@]} ]]; then
# This entire $previous_left thing doesn't make sense.
# I couldn't find a case anywhere, where we would match something
# but not remove something from $left.
break; fi; previous_left=${#left[@]}; done; if [[ $times -ge 1 ]]; then
return 0; fi; return 1; }; optional() { local pattern; for pattern in "$@"; do
$pattern; done; return 0; }; required() { local initial_left=("${left[@]}")
local pattern; local unset_test_match=true
$test_match && unset_test_match=false; test_match=true; for pattern in "$@"; do
if ! $pattern; then left=("${initial_left[@]}")
$unset_test_match && test_match=false; return 1; fi; done
if $unset_test_match; then test_match=false; left=("${initial_left[@]}")
for pattern in "$@"; do $pattern; done; fi; return 0; }; _switch() { local i
for i in "${!left[@]}"; do local l=${left[$i]}
if [[ ${parsed_params[$l]} == "$3" ]]; then
left=("${left[@]:0:$i}" "${left[@]:((i+1))}"); $test_match && return 0
if [[ $2 == true ]]; then eval "(($1++))"; else eval "$1=true"; fi; return 0
fi; done; return 1; }; _value() { local i; local needle=${3:-'a'}
for i in "${!left[@]}"; do local l=${left[$i]}
if [[ ${parsed_params[$l]} == "$needle" ]]; then
left=("${left[@]:0:$i}" "${left[@]:((i+1))}"); $test_match && return 0
local value; value=$(printf -- "%q" "${parsed_values[$l]}")
if [[ $2 == true ]]; then eval "$1+=($value)"; else eval "$1=$value"; fi
return 0; fi; done; return 1; }; parse_shorts() { token=${argv[0]}
argv=("${argv[@]:1}"); [[ $token == -* && $token != --* ]] || assert_fail
local remaining=${token#-}; while [[ -n $remaining ]]; do
short="-${remaining:0:1}"; remaining="${remaining:1}"; local i=0
local similar=(); local similar_idx=false; for o in "${options_short[@]}"; do
if [[ $o == "$short" ]]; then similar+=("$short")
[[ $similar_idx == false ]] && similar_idx=$i; fi; ((i++)); done
if [[ ${#similar[@]} -gt 1 ]]; then
error "$(printf "%s is specified ambiguously %d times" "$short" "${#similar[@]}")"
elif [[ ${#similar[@]} -lt 1 ]]; then similar_idx=${#options_short[@]}
value=true; options_short+=("$short"); options_long+=('')
options_argcount+=(0); else value=false
if [[ ${options_argcount[$similar_idx]} -ne 0 ]]; then
if [[ $remaining == '' ]]; then
if [[ ${#argv[@]} -eq 0 || ${argv[0]} == '--' ]]; then
error "$(printf "%s requires argument" "$short")"; fi; value=${argv[0]}
argv=("${argv[@]:1}"); else value=$remaining; remaining=''; fi; fi
if [[ $value == false ]]; then value=true; fi; fi
parsed_params+=("$similar_idx"); parsed_values+=("$value"); done; }
parse_long() { token=${argv[0]}; long=${token%%=*}; value=${token#*=}
argv=("${argv[@]:1}"); [[ $token == --* ]] || assert_fail
if [[ $token = *=* ]]; then eq='='; else eq=''; value=false; fi; local i=0
local similar=(); local similar_idx=false; for o in "${options_long[@]}"; do
if [[ $o == "$long" ]]; then similar+=("$long")
[[ $similar_idx == false ]] && similar_idx=$i; fi; ((i++)); done
if [[ ${#similar[@]} -eq 0 ]]; then i=0; for o in "${options_long[@]}"; do
if [[ $o == $long* ]]; then similar+=("$long")
[[ $similar_idx == false ]] && similar_idx=$i; fi; ((i++)); done; fi
if [[ ${#similar[@]} -gt 1 ]]; then
error "$(printf "%s is not a unique prefix: %s?" "$long" "${similar[*]}")"
elif [[ ${#similar[@]} -lt 1 ]]; then if [[ $eq == '=' ]]; then argcount=1
else argcount=0; fi; similar_idx=${#options_short[@]}
if [[ argcount -eq 0 ]]; then value=true; fi; options_short+=('')
options_long+=("$long"); options_argcount+=("$argcount"); else
if [[ ${options_argcount[$similar_idx]} -eq 0 ]]; then
if [[ $value != false ]]; then
error "$(printf "%s must not have an argument" "${options_long[$similar_idx]}")"
fi; else if [[ $value == false ]]; then
if [[ ${#argv[@]} -eq 0 || ${argv[0]} == '--' ]]; then
error "$(printf "%s requires argument" "$long")"; fi; value=${argv[0]}
argv=("${argv[@]:1}"); fi; fi; if [[ $value == false ]]; then value=true; fi
fi; parsed_params+=("$similar_idx"); parsed_values+=("$value"); }
parse_argv() { while [[ ${#argv[@]} -gt 0 ]]; do
if [[ ${argv[0]} == "--" ]]; then for arg in "${argv[@]}"; do
parsed_params+=('a'); parsed_values+=("$arg"); done; return
elif [[ ${argv[0]} = --* ]]; then parse_long
elif [[ ${argv[0]} == -* && ${argv[0]} != "-" ]]; then parse_shorts; else
parsed_params+=('a'); parsed_values+=("${argv[0]}"); argv=("${argv[@]:1}"); fi
done; }; help() { printf -- "%s\n" "$doc"; }; error() {
[[ -n $1 ]] && printf "%s\n" "$1"; printf "%s\n" "${doc:13:223}"; exit 1; }
extras() { for idx in "${parsed_params[@]}"; do [[ $idx == 'a' ]] && continue
if [[ ${options_short[$idx]} == "-h" || ${options_long[$idx]} == "--help" ]]; then
help; exit 0; fi; done; for idx in "${parsed_params[@]}"; do
[[ $idx == 'a' ]] && continue
if [[ ${options_long[$idx]} == "--version" ]]; then printf "%s\n" "$version"
exit 0; fi; done; }; setup() { argv=("$@"); options_short=('' '' '' '')
options_long=(--speed --moored --drifting --version)
options_argcount=(1 0 0 0)
param_names=(__speed __moored __drifting __version _name_ _x_ _y_ ship new move shoot mine set remove)
parsed_params=(); parsed_values=(); left=(); test_match=false
for var in "${param_names[@]}"; do unset "$var"; done; }; teardown() {
unset argv options_short options_long options_argcount param_names \
parsed_params parsed_values left test_match
unset -f either oneormore optional required _command _switch _value \
check defaults extras help error docopt \
parse_argv parse_long parse_shorts setup teardown; }; check() {
local current_doc_hash
local digest="4a387f559ae024343f27dbbc69f223c67d0ec7e20082f3bd682c67348ebb208d"
current_doc_hash=$(printf "%s" "$doc" | shasum -a 256 | cut -f 1 -d " ")
if [[ $current_doc_hash != "$digest" ]]; then
printf "The current usage doc (%s) does not match what the parser was generated with (%s)\n" \
"$current_doc_hash" "$digest" >&2; exit 1; fi; }; defaults() {
__speed=${__speed:-10}; __moored=${__moored:-false}
__drifting=${__drifting:-false}; __version=${__version:-false}
[[ -z ${_name_+x} ]] && _name_=(); _x_=${_x_:-}; _y_=${_y_:-}
ship=${ship:-false}; new=${new:-false}; move=${move:-false}
shoot=${shoot:-false}; mine=${mine:-false}; set=${set:-false}
remove=${remove:-false}; }; docopt() { type check &>/dev/null && check
setup "$@"; parse_argv; extras; local i=0
while [[ $i -lt ${#parsed_params[@]} ]]; do left+=("$i"); ((i++)); done
if ! root; then error; fi; type defaults &>/dev/null && defaults
if [[ ${#left[@]} -gt 0 ]]; then error; fi
type teardown &>/dev/null && teardown; return 0; }
# docopt parser above, refresh this parser with `docopt.sh naval_fate.sh`

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
