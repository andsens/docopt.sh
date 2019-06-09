#!/usr/bin/env python3
import sys
import os
import docopt
import logging
import termcolor
from . import __doc__ as pkg_doc, __name__ as root_name, DocoptError, __version__
from .parser import ParserParameters, Parser
from .script import Script

log = logging.getLogger(root_name)

__doc__ = pkg_doc + """
Usage:
  docopt.sh generate-library
  docopt.sh [options] [SCRIPT]

Options:
  --prefix PREFIX    Parameter variable name prefix (default: "")
  --line-length N    Max line length when minifying (0 to disable, default: 80)
  --library -l SRC   Generates only the dynamic part of the parser and includes
                     the static parts using `source SRC`, use `generate-library`
                     to create that file
  --no-auto-params   Disable auto-detection parser generation parameters
  --parser           Output parser instead of inserting it in the script
  -h --help          This help message
  --version          Version of this program

Note:
  You can pass the script on stdin as well,
  docopt.sh will then output the modified script to stdout.

Parameters:
  You can set the following global variables before invoking docopt with
  `docopt "$@"` to change the behavior of docopt.

  $DOCOPT_PROGRAM_VERSION  The string to print when --version is specified
                           [default: none/disabled]
  $DOCOPT_ADD_HELP         Set to `false` to not print usage on --help
                           [default: true]
  $DOCOPT_OPTIONS_FIRST    Set to `true` to fail when options are specified
                           after arguments/commands [default: false]
"""


def docopt_sh(params):
  if params['generate-library']:
    parser = Parser(params)
    sys.stdout.write('#!/usr/bin/env bash\n\n' + str(parser.generate_library(check_version=True)))
  else:
    try:
      if params['SCRIPT'] is None:
        if sys.stdin.isatty():
          raise docopt.DocoptExit(
            'Not reading from stdin when it is a tty. '
            'Use either `docopt.sh script.sh` or `docopt.sh < script.sh`.'
          )
        script = Script(sys.stdin.read())
      else:
        with open(params['SCRIPT'], 'r') as h:
          script = Script(h.read(), params['SCRIPT'])
      script.validate()

      parser_parameters = ParserParameters(params, script)
      parser = Parser(parser_parameters)

      if params['--parser']:
        sys.stdout.write(parser.generate(script))
      else:
        patched_script = script.patch(parser)
        if params['SCRIPT'] is None:
          sys.stdout.write(str(patched_script))
        else:
          with open(params['SCRIPT'], 'w') as h:
            h.write(str(patched_script))
          if patched_script == script:
            log.info('The parser in %s is already up-to-date.', params['SCRIPT'])
          else:
            log.info('%s has been updated.', params['SCRIPT'])
    except DocoptError as e:
      log.error(str(e))
      sys.exit(e.exit_code)


def setup_logging():
  level_colors = {
    logging.ERROR: 'red',
    logging.WARN: 'yellow',
  }

  class ColorFormatter(logging.Formatter):

    def format(self, record):
        record.msg = termcolor.colored(record.msg, level_colors.get(record.levelno, None))
        return super(ColorFormatter, self).format(record)

  stderr = logging.StreamHandler(sys.stderr)
  if os.isatty(2):
    stderr.setFormatter(ColorFormatter())
  log.setLevel(level=logging.INFO)
  log.addHandler(stderr)


def main():
  setup_logging()
  params = docopt.docopt(__doc__, version=__version__)
  docopt_sh(params)

if __name__ == '__main__':
  main()
