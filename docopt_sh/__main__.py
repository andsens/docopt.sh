#!/usr/bin/env python3
import sys
import re
import os
from docopt import docopt, DocoptExit
from . import __doc__ as pkg_doc
from .script import Script, DocoptScriptValidationError
from .parser import Parser
import logging

log = logging.getLogger(__name__)

__doc__ = pkg_doc + """
Usage:
  docopt.sh [options] [SCRIPT]

Parser generation options:
  --prefix=PREFIX  Parameter variable name prefix [default: ]
  --no-doc-check   Disable check for whether if the parser matches the doc
  --no-help        Disable automatic help on -h or --help
  --options-first  Require that options precede positional arguments
  --no-teardown    Disable teardown of functions and variables after parsing
  --no-version     Disable automatic --version despite $version being present
  --no-minimize    Disable parsing code minimization
  --line-length N  Maximum line length when minimizing [default: 80]

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
  try:
    if params['SCRIPT'] is None:
      if sys.stdin.isatty():
        raise DocoptExit('Not reading from stdin when it is a tty')
      script = Script(sys.stdin.read())
    else:
      with open(params['SCRIPT'], 'r') as h:
        script = Script(h.read(), params['SCRIPT'])
    parser = Parser(script, params)
    if params['--only-parser']:
      sys.stdout.write(str(parser))
    else:
      patched_script = str(parser.patched_script)
      if params['SCRIPT'] is None:
        sys.stdout.write(patched_script)
      else:
        with open(params['SCRIPT'], 'w') as h:
          h.write(patched_script)
  except DocoptScriptValidationError as e:
    print(str(e))
    # Exit code 74: input/output error (sysexits.h)
    sys.exit(74)


def main():
  params = docopt(__doc__)
  docopt_sh(params)

if __name__ == '__main__':
  main()
