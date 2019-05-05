#!/usr/bin/env bash

docopt_teardown() {
  unset argv options_short options_long options_argcount param_names \
  parsed_params parsed_values left test_match
  unset -f either oneormore optional required _command _switch _value \
  docopt_check docopt_defaults docopt_extras docopt_help docopt_error docopt \
  parse_argv parse_long parse_shorts docopt_setup docopt_teardown
}
