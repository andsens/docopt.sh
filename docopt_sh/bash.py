import re
from shlex import quote
from itertools import chain


class Code(object):

  def __init__(self, code):
    self.code = self._get_iter(code)

  def _get_iter(self, code):
    if isinstance(code, str):
      return iter([code])
    else:
      return iter(code)

  def minify(self, max_line_length):
    return Code(minify(str(self), max_line_length))

  def replace_literal(self, replacements):
    def gen_replace():
      for part in self.code:
        code = str(part)
        for placeholder, replacement in replacements.items():
          code = code.replace(placeholder, str(replacement))
        yield code
    return Code(gen_replace())

  def __iter__(self):
    return self.code

  def __add__(self, other):
    return Code(chain(self.code, self._get_iter(other)))

  def __str__(self):
    return '\n'.join(map(str, self))


def indent(script, level=1):
  indentation = '  ' * level

  def indent_line(line):
    return indentation + line if line else line
  return '\n'.join(map(indent_line, script.split('\n')))


def bash_variable_name(name):
  return re.sub(r'^[^a-z_]|[^a-z0-9_]', '_', name, 0, re.IGNORECASE)


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


def minify(parser_str, max_length):
  lines = parser_str.split('\n')
  lines = remove_leading_spaces(lines)
  lines = remove_empty_lines(lines)
  lines = remove_comments(lines)
  lines = remove_newlines(lines, max_length)
  return '\n'.join(lines) + '\n'


def remove_leading_spaces(lines):
  for line in lines:
    yield re.sub(r'^\s*', '', line)


def remove_empty_lines(lines):
  for line in lines:
    if line != '':
      yield line


def remove_comments(lines):
  for line in lines:
    if re.match(r'^\s*#', line) is None:
      yield line


def remove_newlines(lines, max_length):
  def needs_separator(line):
    return re.search(r'; (then|do)$|else$|\{$', line) is None

  def has_continuation(line):
    return re.search(r'\\\s*$', line) is not None

  def remove_continuation(line):
    return re.sub(r'\s*\\\s*$', '', line)

  def combine(line1, line2):
    if has_continuation(line1):
      return remove_continuation(line1) + ' ' + line2
    if needs_separator(line1):
      return line1 + '; ' + line2
    else:
      return line1 + ' ' + line2

  previous = next(lines)
  for line in lines:
    combined = combine(previous, line)
    if len(combined) > max_length:
      yield previous
      previous = line
    else:
      previous = combined
  if previous:
    yield previous
