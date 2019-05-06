#!/usr/bin/env python3
import sys
import re
import os
import docopt
from docopt_sh.patcher import find_doc, insert_parser
from docopt_sh.parser import parse_doc
from docopt_sh.generator import generate_parser, generate_doc_check, generate_teardown

__doc__ = """
docopt.sh
  Bash argument parser generator.
  This program looks for a "doc" variable in SCRIPT
  and appends a matching parser to it.

Usage:
  docopt.sh [options] [SCRIPT]

Parser generation options:
  -p --prefix=PREFIX  Naming prefix for the argument variables [default: ]
  -c --no-doc-check   Disable check for whether if the parser matches the doc
  -n --no-help        Disable automatic help on -h or --help
  -f --options-first  Require that options precede positional arguments
  -t --no-teardown    Do not tear down functions or variables after parsing

Other options:
  -o --only-parser    Only output the parser to stdout
  -d --debug          Whether to enable debugging mode (embedded in the parser)
  -h --help           This help message
  -v --version        Version of this program


Notes:
  You can pass the script on stdin as well,
  docopt.sh will then output the modified script to stdout.

  If the script has a $version defined before the variable usage doc variable
  --version will automatically output the value of that variable.
"""


def docopt_sh(params):
    if params['SCRIPT'] is None:
        script = sys.stdin.read()
    else:
        with open(params['SCRIPT'], 'r') as h:
            script = h.read()
    doc, docname, lines = find_doc(script)
    pattern = parse_doc(doc)
    parser = generate_parser(pattern, docname, debug=params['--debug'])
    if not params['--no-teardown']:
        parser += generate_teardown()
    if not params['--no-doc-check']:
        parser += generate_doc_check(parser, doc, docname)
    if params['--only-parser']:
        sys.stdout.write(parser)
    else:
      patched_script = insert_parser(script, lines, parser, params)
      if params['SCRIPT'] is None:
          sys.stdout.write(patched_script)
      else:
          with open(params['SCRIPT'], 'w') as h:
              h.write(patched_script)

def main():
    params = docopt.docopt(__doc__)
    docopt_sh(params)

if __name__ == '__main__':
    main()
