import re
from shlex import quote


def bash_name(name, prefix=''):
  name = name.replace('<', '_')
  name = name.replace('>', '_')
  name = name.replace('-', '_')
  name = name.replace(' ', '_')
  return prefix + name


def bash_value(value):
  if value is None:
    return ''
  if type(value) is bool:
    return 'true' if value else 'false'
  if type(value) is int:
    return str(value)
  if type(value) is str:
    return quote(value)
  if type(value) is list:
    return '(%s)' % ' '.join(bash_value(v) for v in value)
  raise Exception('Unknown value type %s' % type(value))


def bash_array_value(value):
  if value is None or value == '':
    return "''"
  if type(value) is bool:
    return 'true' if value else 'false'
  if type(value) is int:
    return str(value)
  if type(value) is str:
    return quote(value)
  if type(value) is list:
    raise Exception('Unable to convert list to bash array value')
  raise Exception('Unknown value type %s' % type(value))


def minimize(parser_str, max_length):
  lines = parser_str.split('\n')
  lines = remove_leading_spaces(lines)
  lines = remove_empty_lines(lines)
  lines = remove_newlines(lines, max_length)
  return '\n'.join(lines)


def remove_leading_spaces(lines):
  for line in lines:
    yield re.sub(r'^\s*', '', line)


def remove_empty_lines(lines):
  for line in lines:
    if line != '':
      yield line


def remove_newlines(lines, max_length):
  no_separator = re.compile(r'; (then|do)$|else$|\{$')
  comment = re.compile(r'^\s*#')
  current = None
  for line in lines:
    if not current:
      current = line
      continue
    if comment.match(line):
      if current:
        yield current
      yield line
      current = None
      continue
    separator = ' ' if no_separator.search(current) else '; '
    if len(current + separator + line) < max_length:
      current += separator + line
    else:
      yield current
      current = line
  if current != '':
    yield current
