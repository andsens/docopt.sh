import re
import logging
import shlex
import docopt
from . import DocoptError

log = logging.getLogger(__name__)


class Script(object):

  def __init__(self, contents, path=None):
    self.contents = contents
    self.path = path

    self.doc = Doc(self)
    self.guards = Guards(self, self.doc)
    self.invocation = Invocation(self, self.guards)
    self.options = [Option(self, name) for name in [
      'docopt_program_version', 'docopt_add_help', 'docopt_options_first',
      'docopt_teardown', 'docopt_doc_check', 'docopt_lib_check'
    ]]

  def validate(self):
    if not self.doc.present:
      raise DocoptScriptValidationError('Could not find variable containing usage doc.', self.doc)
    if self.doc.count > 1:
      raise DocoptScriptValidationError('More than one variable containing usage doc found.', self.doc)
    if self.guards.top.count > 1:
      raise DocoptScriptValidationError('Multiple docopt parser start guards found.', self.guards.top)
    if self.guards.bottom.count > 1:
      raise DocoptScriptValidationError('Multiple docopt parser end guards found.', self.guards.bottom)
    if self.guards.top.present and not self.guards.bottom.present:
        raise DocoptScriptValidationError(
          'Parser begin guard found, but no end guard detected.', self.guards.top)
    if self.guards.bottom.present and not self.guards.top.present:
      raise DocoptScriptValidationError(
        'Parser end guard found, but no begin guard detected.', self.guards.bottom)
    if self.invocation.count > 1:
      log.warning(
        '%s Multiple invocations of docopt found, check your script to make sure this is correct.',
        self.invocation
      )
    if not self.invocation.present:
      log.warning(
        '%s No invocations of docopt found, check your script to make sure this is correct.\n'
        'docopt.sh is invoked with `docopt "$@"`.',
        self.invocation
      )
    for option in self.options:
      if option.present and option.start > self.invocation.last.end:
        log.warning(
          '%s $%s has no effect when specified after invoking docopt, '
          'make sure to place docopt options before calling `docopt "$@"`.',
          option, option.name
        )

  def patch(self, parser):
    return Script(
      "{start}{guard_begin}\n{parser}{guard_end}\n{end}".format(
        start=self.contents[:self.guards.start],
        guard_begin="# docopt parser below, refresh this parser with `%s`" % parser.parameters.refresh_command,
        parser=parser.generate(self),
        guard_end="# docopt parser above, refresh this parser with `%s`" % parser.parameters.refresh_command,
        end=self.contents[self.guards.end:],
      )
    )

  def __eq__(self, other):
    return self.contents == other.contents

  def __str__(self):
    return self.contents


class ScriptLocation(object):

  def __init__(self, script, matches, offset):
    self.script = script
    self.matches = list(matches)
    self.match = self.matches[0] if self.matches else None
    self.offset = 0 if offset is None else offset

  def __len__(self):
    return self.end - self.start if self.present else 0

  @property
  def all(self):
    return [ScriptLocation(self.script, iter([match]), self.offset) for match in self.matches]

  @property
  def last(self):
    return ScriptLocation(self.script, iter([self.matches[-1]]), self.offset)

  @property
  def present(self):
    return self.match is not None

  @property
  def count(self):
    return len(self.matches)

  @property
  def start(self):
    if self.present:
      return self.match.start(0) + self.offset

  @property
  def end(self):
    if self.present:
      return self.match.end(0) + self.offset

  @property
  def line(self):
    return self.script.contents[:self.start].count('\n') + 1

  def __str__(self):
    if not self.present:
      return '%s' % self.script.path
    if self.count > 1:
      return '%s:%s' % (self.script.path, ','.join(map(lambda l: str(l.line), self.all)))
    else:
      return '%s:%d' % (self.script.path, self.line)


class Doc(ScriptLocation):

  def __init__(self, script):
    matches = re.finditer(
      r'([a-zA-Z_][a-zA-Z_0-9]*)="(\s*)(.*?\bUsage:.+?)(\s*)"(\n|;)',
      script.contents,
      re.MULTILINE | re.IGNORECASE | re.DOTALL
    )
    super(Doc, self).__init__(script, matches, 0)

  @property
  def name(self):
    if self.present:
      return self.match.group(1)

  @property
  def value(self):
    if self.present:
      return self.match.group(3)

  @property
  def in_string_value_match(self):
    return self.match.start(3) - self.match.start(2), self.match.end(3) - self.match.end(2)


class Guard(ScriptLocation):

  @property
  def refresh_command(self):
    if self.present:
      return self.match.group(2)
    else:
      return None

  @property
  def refresh_command_params(self):
    if self.refresh_command is not None:
      from .__main__ import __doc__
      try:
        return docopt.docopt(__doc__, shlex.split(self.refresh_command)[1:])
      except (docopt.DocoptLanguageError, docopt.DocoptExit):
        pass


class TopGuard(Guard):

  def __init__(self, script, doc):
    matches = re.finditer(
      r'# docopt parser below(, refresh this parser with `([^`]+)`)?\n',
      script.contents[doc.end:],
      re.MULTILINE
    )
    super(TopGuard, self).__init__(script, matches, doc.end)


class BottomGuard(Guard):

  def __init__(self, script, top):
    matches = re.finditer(
      r'# docopt parser above(, refresh this parser with `([^`]+)`)?\n',
      script.contents[top.end:],
      re.MULTILINE
    )
    super(BottomGuard, self).__init__(script, matches, top.end)


class Guards(object):

  def __init__(self, script, doc):
    self.top = TopGuard(script, doc)
    if self.top.present:
      self.bottom = BottomGuard(script, self.top)
    else:
      self.bottom = BottomGuard(script, doc)

  def __len__(self):
    return self.end - self.start if self.present else 0

  @property
  def present(self):
    return self.top.present and self.bottom.present

  @property
  def start(self):
    if self.present:
      return self.top.start
    else:
      # Convenience location to easily handle none-presence of parser
      return self.top.offset

  @property
  def end(self):
    if self.present:
      return self.bottom.end
    else:
      return self.top.offset

  @property
  def refresh_command_params(self):
    params = self.top.refresh_command_params
    if params is None:
      params = self.bottom.refresh_command_params
    return params


class Invocation(ScriptLocation):

  def __init__(self, script, parser):
    matches = re.finditer(r'docopt\s+"\$\@"', script.contents[parser.end:])
    super(Invocation, self).__init__(script, matches, parser.end)


class Option(ScriptLocation):

  def __init__(self, script, name):
    self.name = name
    matches = re.finditer(r'^%s=' % name, script.contents, re.MULTILINE)
    super(Option, self).__init__(script, matches, 0)
    if self.count > 1:
      # Override parent class selection of first match, previous assignments
      # would be overwritten so it's the last match that has an effect
      self.match = matches[-1]


class DocoptScriptValidationError(DocoptError):

  def __init__(self, message, script_location=None):
    # Exit code 74: input/output error (sysexits.h)
    super(DocoptScriptValidationError, self).__init__(message, exit_code=74)
    self.script_location = script_location

  def __str__(self):
    if self.script_location is not None:
      return '%s %s' % (self.script_location, self.message)
    return self.message
