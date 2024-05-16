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
  lines = continuate_spaces(lines)
  lines = split_sq_strings(lines)
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
    if re.match(r'\s*#', line) is None:
      yield line


def continuate_spaces(lines):
  for line in lines:
    # Split whenever there's a space, but make sure to keep single quoted
    # strings on one line
    yield from re.sub(r"('[^']* [^']*')|( )", r'\1\2\\\n', line).split('\n')


def split_sq_strings(lines):
  for line in lines:
    # Split every character in a single quoted string
    yield from re.sub(
      r"'([^']+)'",
      lambda sq: ''.join(map(lambda c: f"'{c}'\\\n", sq.group(1))),
      line,
    ).split('\n')


def remove_newlines(lines, max_length):
  def get_seperator(line):
    return ';' if re.search(r'(then|do|else|\{)$', line) is None else ' '

  def has_continuation(line):
    return re.search(r'\\\s*$', line) is not None

  def remove_continuation(line):
    return re.sub(r'\\(\s*)$', r'\1', line)

  def combine(line1, line2):
    if has_continuation(line1):
      return remove_continuation(line1) + line2
    return line1 + get_seperator(line1) + line2

  previous = next(lines)
  for line in lines:
    combined = combine(previous, line)
    combined = merge_sq_strings(combined)
    if len(combined) > max_length:
      yield previous
      previous = line
    else:
      previous = combined
  if previous:
    yield previous


def merge_sq_strings(line):
  # We don't need to look for more than a single pair, because
  # all strings were on their own line and remove_newlines()
  # merges one line at a time
  return re.sub(r"'([^']+)''([^']+)'", r"'\1\2'", line)
