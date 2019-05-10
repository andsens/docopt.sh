#!/usr/bin/env python3
import sys
import re
import os
import docopt
from docopt_sh.script import Script
from docopt_sh.generator import generate_parser

__doc__ = """
docopt.sh
  Bash argument parser generator.
  This program looks for a "doc" variable in SCRIPT
  and appends a matching parser to it.

Usage:
  docopt.sh [options] [SCRIPT]

Parser generation options:
  --prefix=PREFIX  Parameter variable name prefix [default: ]
  --no-doc-check   Disable check for whether if the parser matches the doc
  --no-help        Disable automatic help on -h or --help
  --options-first  Require that options precede positional arguments
  --no-teardown    Do not tear down functions or variables after parsing
  --no-version     Do not add --version despite $version being present

Other options:
  --only-parser    Only output the parser to stdout
  -d --debug       Whether to enable debugging mode (embedded in the parser)
  -h --help        This help message
  --version        Version of this program


Notes:
  You can pass the script on stdin as well,
  docopt.sh will then output the modified script to stdout.

  If the script has a $version defined anywhere before the invocation of docopt
  --version will automatically output the value of that variable.
"""


def docopt_sh(params):
  if params['SCRIPT'] is None:
    script = Script(sys.stdin.read())
  else:
    with open(params['SCRIPT'], 'r') as h:
      script = Script(h.read(), params['SCRIPT'])
  parser = generate_parser(script, params)
  if params['--only-parser']:
    sys.stdout.write(parser)
  else:
    refresh_command = generate_refresh_command(params)
    patched_script = script.insert_parser(parser, refresh_command)
    if params['SCRIPT'] is None:
      sys.stdout.write(str(patched_script))
    else:
      with open(params['SCRIPT'], 'w') as h:
        h.write(str(patched_script))

def generate_refresh_command(params):
  command = 'docopt.sh'
  if params['--debug']:
    command += ' --debug'
  if params['--prefix'] != '':
    command += ' --prefix=' + params['--prefix']
  if params['SCRIPT'] is not None:
    command += ' ' + params['SCRIPT']
  return command

def main():
  params = docopt.docopt(__doc__)
  docopt_sh(params)

if __name__ == '__main__':
  main()
