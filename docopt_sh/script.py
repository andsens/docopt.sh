import re
import logging

log = logging.getLogger(__name__)


class Script(object):

  def __init__(self, contents, path=None):
    self.contents = contents
    self.path = path

    self.doc = Doc(self.contents)
    self.parser = Parser(self.contents, self.doc)
    self.invocation = Invocation(self.contents, self.parser)
    self.version = Version(self.contents, self.invocation)
    self.validate_script_locations()

  def validate_script_locations(self):
    if not self.doc.present:
      raise DocoptScriptValidationError('Variable containing usage doc not found.', self.path)
    if self.doc.count > 1:
      raise DocoptScriptValidationError('More than one variable contain usage doc found.', self.path)
    if self.parser.start_guard.count > 1:
      raise DocoptScriptValidationError('Multiple docopt parser start guards found', self.path)
    if self.parser.end_guard.count > 1:
      raise DocoptScriptValidationError('Multiple docopt parser end guards found', self.path)
    if self.parser.start_guard.present and not self.parser.end_guard.present:
        raise DocoptScriptValidationError('Parser begin guard found, but no end guard detected', self.path)
    if self.parser.end_guard.present and not self.parser.start_guard.present:
      raise DocoptScriptValidationError('Parser end guard found, but no begin guard detected', self.path)
    if self.invocation.count > 1:
      log.warning('Multiple invocations of docopt found, check your script to make sure this is correct.')
    if not self.invocation.present:
      log.warning(
        'No invocations of docopt found, check your script to make sure this is correct.\n'
        'docopt.sh is invoked with `docopt "$@"`'
      )

  def insert_parser(self, parser, refresh_command=None):
    guard_begin = "# docopt parser below"
    guard_end = "# docopt parser above"
    if refresh_command:
      guard_begin += ", refresh this parser with `%s`" % refresh_command
      guard_end += ", refresh this parser with `%s`" % refresh_command
    return Script(
      "{start}{guard_begin}\n{parser}{guard_end}\n{end}".format(
        start=self.contents[:self.parser.start],
        guard_begin=guard_begin,
        parser=parser,
        guard_end=guard_end,
        end=self.contents[self.parser.end:],
      )
    )

  def __str__(self):
    return self.contents


class ScriptLocation(object):

  def __init__(self, matches, offset):
    self.matches = matches
    self.match = next(matches, None)
    self.offset = 0 if offset is None else offset

  def __len__(self):
    return self.end - self.start if self.present else 0

  @property
  def present(self):
    return self.match is not None

  @property
  def count(self):
    return len(list(self.matches))

  @property
  def start(self):
    if self.present:
      return self.match.start(0) + self.offset

  @property
  def end(self):
    if self.present:
      return self.match.end(0) + self.offset


class Doc(ScriptLocation):

  def __init__(self, script):
    matches = re.finditer(
      r'([a-zA-Z_][a-zA-Z_0-9]*)="((\\"|[^"])*Usage:(\\"|[^"])+)"\s*(\n|;)',
      script,
      re.MULTILINE | re.IGNORECASE
    )
    super(Doc, self).__init__(matches, 0)

  @property
  def name(self):
    if self.present:
      return self.match.group(1)

  @property
  def value(self):
    if self.present:
      return self.match.group(2)


class ParserStartGuard(ScriptLocation):

  def __init__(self, script, doc):
    matches = re.finditer(r'# docopt parser below[^\n]*\n', script[doc.end:], re.MULTILINE)
    super(ParserStartGuard, self).__init__(matches, doc.end)


class ParserEndGuard(ScriptLocation):

  def __init__(self, script, start_guard):
    matches = re.finditer(r'# docopt parser above[^\n]*\n', script[start_guard.end:], re.MULTILINE)
    super(ParserEndGuard, self).__init__(matches, start_guard.end)


class Parser(object):

  def __init__(self, script, doc):
    self.start_guard = ParserStartGuard(script, doc)
    if self.start_guard.present:
      self.end_guard = ParserEndGuard(script, self.start_guard)
    else:
      self.end_guard = ParserEndGuard(script, doc)

  def __len__(self):
    return self.end - self.start if self.present else 0

  @property
  def present(self):
    return self.start_guard.present and self.end_guard.present

  @property
  def start(self):
    if self.present:
      return self.start_guard.start
    else:
      # Convenience location to easily handle none-presence of parser
      return self.start_guard.offset

  @property
  def end(self):
    if self.present:
      return self.end_guard.end
    else:
      return self.start_guard.offset


class Invocation(ScriptLocation):

  def __init__(self, script, parser):
    matches = re.finditer(r'docopt\s+"\$\@"', script[parser.end:])
    super(Invocation, self).__init__(matches, parser.end)


class Version(ScriptLocation):

  def __init__(self, script, invocation):
    matches = re.finditer(r'^version=', script[:invocation.start], re.MULTILINE)
    super(Version, self).__init__(matches, 0)
    if self.count > 1:
      # Override parent class selection of first match, previous assignments
      # would be overwritten so it's the last match that has an effect
      self.match = matches[-1]


class DocoptScriptValidationError(Exception):

  def __init__(self, message, path=None):
    super(DocoptScriptValidationError, self).__init__(message)
    self.message = message
    self.path = path

  def __str__(self):
    if self.path:
      return 'Error in %s: %s' % (self.path, self.message)
    return self.message
