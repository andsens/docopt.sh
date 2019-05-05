#!/usr/bin/env python3
import sys
import re
from shlex import quote
import os
import docopt
from patcher import find_doc, insert_parser
from parser import parse_doc
from generator import generate_parser, generate_doc_check, generate_invocation

__all__ = ['docopt_sh']
__version__ = '0.0.0'
__doc__ = """
docopt.sh
  Bash argument parser generator.
  This program looks for a "doc" variable in SCRIPT.sh
  and appends a matching parser to it.

Usage:
  docopt.sh [options] [SCRIPT]

Options:
  -d --docname=NAME   Variable name to look for in the script [default: doc]
  -p --prefix=PREFIX  Naming prefix for the argument variables [default: ]
  -c --no-doc-check   Don't add a test to check if the parser is up to date
                      with the usage doc
  -d --debug          Whether to enable debugging mode (embedded in the parser)
  -h --help           This help message
  -v --version        Version of this program

Note:
  You can pass the script on stdin as well,
  docopt.sh will then output the modified script to stdout.
"""


def docopt_sh(params):
    if params['SCRIPT'] is None:
        script = sys.stdin.read()
    else:
        with open(params['SCRIPT'], 'r') as h:
            script = h.read()
    docname = params['--docname']
    doc, lines = find_doc(script, docname)
    pattern = parse_doc(doc)
    parser = generate_parser(pattern, docname, debug=params['--debug'])
    if not params['--no-doc-check']:
        parser += generate_doc_check(parser, doc, docname)
    parser += generate_invocation(parser)
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
