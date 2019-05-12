import re
from shlex import quote


class Function(object):

  def __init__(self, settings, name):
    self.name = name
    self.settings = settings

  def fn_wrap(self, body):
    indented = '\n'.join(['  ' + line for line in body.strip().split('\n')])
    return '{name}() {{\n{body}\n}}'.format(name=self.name, body=indented)

  def __str__(self):
    return self.fn_wrap(self.body)


def bash_variable_name(name, prefix=''):
  name = name.replace('<', '_')
  name = name.replace('>', '_')
  name = name.replace('-', '_')
  name = name.replace(' ', '_')
  return prefix + name


def bash_variable_value(value):
  if value is None:
    return ''
  if type(value) is bool:
    return 'true' if value else 'false'
  if type(value) is int:
    return str(value)
  if type(value) is str:
    return quote(value)
  if type(value) is list:
    return '(%s)' % ' '.join(bash_variable_value(v) for v in value)
  raise Exception('Unhandled value type %s' % type(value))


def bash_ifs_value(value):
  if value is None or value == '':
    return "''"
  if type(value) is bool:
    return 'true' if value else 'false'
  if type(value) is int:
    return str(value)
  if type(value) is str:
    return quote(value)
  if type(value) is list:
    raise Exception('Unable to convert list to bash value intended for an IFS separated field')
  raise Exception('Unhandled value type %s' % type(value))


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
  def is_comment(line):
    return re.match(r'^\s*#', line) is not None

  def needs_separator(line):
    return re.search(r'; (then|do)$|else$|\{$', line) is None

  def has_continuation(line):
    return re.search(r'\\\s*$', line) is not None

  def remove_continuation(line):
    return re.sub(r'\s*\\\s*$', '', line)

  def combine(line1, line2):
    if is_comment(line1) or is_comment(line2):
      if not is_comment(line1):
        return line1
      if not is_comment(line2):
        return line2
      return None
    if has_continuation(line1):
      return remove_continuation(line1) + ' ' + line2
    if needs_separator(line1):
      return line1 + '; ' + line2
    else:
      return line1 + ' ' + line2

  previous = next(lines)
  for line in lines:
    combined = combine(previous, line)
    if combined is None:
      previous = next(lines, None)
    elif len(combined) > max_length:
      yield previous
      previous = line
    else:
      previous = combined
  if previous:
    yield previous
