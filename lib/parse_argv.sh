#!/usr/bin/env bash

parse_argv() {
# def parse_argv(tokens, options, options_first=False):
# """Parse command-line argument vector.

# If options_first:
#   argv ::= [ long | shorts ]* [ argument ]* [ '--' [ argument ]* ] ;
# else:
#   argv ::= [ long | shorts | argument ]* [ '--' [ argument ]* ] ;

# """
# parsed = []
  while [[ ${#argv[@]} -gt 0 ]]; do
# while tokens.current() is not None:
    if [[ ${argv[0]} == "--" ]]; then
#   if tokens.current() == '--':
      for arg in "${argv[@]}"; do
        parsed_params+=('a')
        parsed_values+=("$arg")
      done
      return
#     return parsed + [Argument(None, v) for v in tokens]
    elif [[ ${argv[0]} = --* ]]; then
#   elif tokens.current().startswith('--'):
      parse_long
#     parsed += parse_long(tokens, options)
    elif [[ ${argv[0]} == -* && ${argv[0]} != "-" ]]; then
#   elif tokens.current().startswith('-') and tokens.current() != '-':
      parse_shorts
#     parsed += parse_shorts(tokens, options)
    elif $options_first; then
#   elif options_first:
      for arg in "${argv[@]}"; do
        parsed_params+=('a')
        parsed_values+=("$arg")
      done
      return
#     return parsed + [Argument(None, v) for v in tokens]
    else
#   else:
      parsed_params+=('a')
      parsed_values+=("${argv[0]}")
      argv=("${argv[@]:1}")
#     parsed.append(Argument(None, tokens.move()))
    fi
  done
# return parsed
}
