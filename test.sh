#!/usr/bin/env bash

# shellcheck source=lib/parse_argv.sh
source "lib/parse_argv.sh"
# shellcheck source=lib/parse_long.sh
source "lib/parse_long.sh"
# shellcheck source=lib/parse_shorts.sh
source "lib/parse_shorts.sh"
# shellcheck source=lib/required.sh
source "lib/required.sh"

# def docopt(doc, argv=None, help=True, version=None, options_first=False):
test() {
  local doc_name='simple_command'
  local doc
  doc=$(cat "usage/$doc_name.txt")
  # local help=true
  # local version=''
  options_first=false
  local out
  printf "#!/usr/bin/env bash\n\n" > parser.sh
  ./docopt.py <<<"$doc" >> parser.sh
  cat parser.sh
  source parser.sh

  docopt "$@"

  debug_var "left" "${left[@]}"
  debug_var "options_long" "${options_long[@]}"
  debug_var "parsed_params" "${parsed_params[@]}"
  debug_var "parsed_values" "${parsed_values[@]}"
  for var in "${param_names[@]}"; do
    debug_var "$var" "$(eval "echo \$$var")"
  done
}

debug_var() {
  local varname=$1
  shift
  printf -- "%s" "$varname"
  if [[ $# -eq 1 ]]; then
    printf -- ": %s" "$1"
  else
    printf -- " (%d): " "$#"
    printf -- "'%s' " "$@"
  fi
  printf "\n"
}

die() {
  # shellcheck disable=2059
  printf "$1\n" "$2" >&2
  exit 1
}

test "$@"
