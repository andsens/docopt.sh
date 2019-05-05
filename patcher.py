import re
from parser import DocoptLanguageError

def find_doc(script, docname):
    matches = list(re.finditer(r'%s="((\\"|[^"])+Usage:(\\"|[^"])+)"' % re.escape(docname), script, re.MULTILINE | re.IGNORECASE))
    if len(matches) == 0:
        raise DocoptLanguageError('"%=" (case-insensitive) not found.' % docname)
    if len(matches) > 1:
        raise DocoptLanguageError('More than one "%s=" (case-insensitive).' % docname)
    doc = matches[0].group(1)
    doc_end = matches[0].end(0)

    parser_begin = doc_end
    matches = list(re.finditer(r'# docopt parser below', script))
    if len(matches) > 1:
        raise DocoptLanguageError('Multiple docopt parser start guards found')
    if len(matches) == 1:
        parser_begin = matches[0].start(0)

    parser_end = doc_end
    matches = list(re.finditer(r'# docopt parser above .*', script))
    if len(matches) > 1:
        raise DocoptLanguageError('Multiple docopt parser end guards found')
    if len(matches) == 1:
        parser_end = matches[0].end(0)

    return doc, (doc_end, parser_begin, parser_end)

def insert_parser(script, lines, parser, params):
    doc_end, parser_begin, parser_end = lines
    command = generate_refresh_command(params)
    guard_begin = "# docopt parser below, refresh this parser with `%s`\n" % format(command)
    guard_end = "# docopt parser above, refresh this parser with `%s`\n" % format(command)
    patched_script = script[0:doc_end]
    return \
      script[0:parser_begin] + \
      "\n" + \
      guard_begin + \
      parser + \
      guard_end + \
      script[parser_end:]

def generate_refresh_command(params):
    command = 'docopt.sh'
    if params['--debug']:
        command += ' --debug'
    if params['--docname'] != 'doc':
        command += ' --docname=' + params['--docname']
    if params['--prefix'] != '':
        command += ' --prefix=' + params['--prefix']
    if params['SCRIPT'] is not None:
        command += ' ' + params['SCRIPT']
    return command
