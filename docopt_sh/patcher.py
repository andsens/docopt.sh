import re
from docopt_sh.parser import DocoptLanguageError
import logging

log = logging.getLogger(__name__)

def find_doc(script):
    matches = list(re.finditer(r'([a-zA-Z_][a-zA-Z_0-9]*)="((\\"|[^"])*Usage:(\\"|[^"])+)"', script, re.MULTILINE | re.IGNORECASE))
    if len(matches) == 0:
        raise DocoptLanguageError('Variable containing usage doc not found.')
    if len(matches) > 1:
        raise DocoptLanguageError('More than one variable contain usage doc found.')
    docname = matches[0].group(1)
    doc = matches[0].group(2)
    doc_end = matches[0].end(0)

    parser_begin = None
    matches = list(re.finditer(r'# docopt parser below', script))
    if len(matches) > 1:
        raise DocoptLanguageError('Multiple docopt parser start guards found')
    if len(matches) == 1:
        parser_begin = matches[0].start(0)

    parser_end = None
    matches = list(re.finditer(r'# docopt parser above.*', script))
    if len(matches) > 1:
        raise DocoptLanguageError('Multiple docopt parser end guards found')
    if len(matches) == 1:
        if parser_begin is None:
          raise DocoptLanguageError('Parser end guard found, but no begin guard detected')
        parser_end = matches[0].end(0)
    else:
      if parser_begin is not None:
        raise DocoptLanguageError('Parser begin guard found, but no end guard detected')

    matches = list(re.finditer(r'docopt\s+"\$\@"', script))
    if len(matches) > 1:
        log.warn('Multiple invocations of docopt found, check your script to make sure this is correct.')
    if len(matches) == 0:
        log.warn('No invocations of docopt found, check your script to make sure this is correct.\ndocopt.sh is invoked with `docopt "$@"`')

    return doc, docname, (doc_end, parser_begin, parser_end)

def insert_parser(script, lines, parser, params):
    doc_end, parser_begin, parser_end = lines
    command = generate_refresh_command(params)
    guard_begin = "# docopt parser below, refresh this parser with `%s`\n" % format(command)
    guard_end = "# docopt parser above, refresh this parser with `%s`" % format(command)
    patched_script = script[0:doc_end]
    doc_spacer = ''
    if parser_begin is None:
        parser_begin = parser_end = doc_end
        doc_spacer = "\n"
    return \
      script[0:parser_begin] + \
      doc_spacer + \
      guard_begin + \
      parser + \
      guard_end + \
      script[parser_end:]

def generate_refresh_command(params):
    command = 'docopt.sh'
    if params['--debug']:
        command += ' --debug'
    if params['--prefix'] != '':
        command += ' --prefix=' + params['--prefix']
    if params['SCRIPT'] is not None:
        command += ' ' + params['SCRIPT']
    return command
