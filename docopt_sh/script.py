import re
import logging
import shlex
import docopt
import subprocess
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
      'DOCOPT_ADD_HELP', 'DOCOPT_PROGRAM_VERSION', 'DOCOPT_OPTIONS_FIRST',
      'DOCOPT_PREFIX', 'DOCOPT_DOC_CHECK', 'DOCOPT_LIB_CHECK'
    ]]

  def validate(self):
    if not self.doc.present:
      raise DocoptScriptValidationError(
        'Could not find variable containing usage doc. '
        'Make sure your script contains a `DOC="... Usage: ..."` variable',
        self.doc
      )
    if self.doc.count > 1:
      raise DocoptScriptValidationError(
        'More than one variable containing usage doc found. '
        'Search your script for `DOC=`, there should be only one such declaration.',
        self.doc
      )
    guard_help = (
        'Search your script for `# docopt parser below/above`, '
        'there should be exactly one with `below` and one with `above` (in that order). '
        'If in doubt, just delete anything that is not your code and try again.'
    )
    if self.guards.top.count > 1:
      raise DocoptScriptValidationError(
        'Multiple docopt parser top guards found. ' + guard_help, self.guards.top)
    if self.guards.bottom.count > 1:
      raise DocoptScriptValidationError(
        'Multiple docopt parser bottom guards found.' + guard_help, self.guards.bottom)
    if self.guards.top.present and not self.guards.bottom.present:
        raise DocoptScriptValidationError(
          'Parser top guard found, but no bottom guard detected. ' + guard_help, self.guards.top)
    if self.guards.bottom.present and not self.guards.top.present:
      raise DocoptScriptValidationError(
        'Parser bottom guard found, but no top guard detected. ' + guard_help, self.guards.bottom)
    if self.invocation.count > 1:
      log.warning(
        '%s Multiple invocations of docopt found, check your script to make sure this is correct.',
        self.invocation
      )
    if not self.invocation.present:
      log.warning(
        '%s No invocations of docopt found, check your script to make sure this is correct.\n'
        'docopt.sh is invoked with `eval "$(docopt "$@")"`.',
        self.invocation
      )
    for option in self.options:
      if self.invocation.present and option.present and option.start > self.invocation.last.end:  # type: ignore
        log.warning(
          '%s $%s has no effect when specified after invoking docopt, '
          'make sure to place docopt options before calling `eval "$(docopt "$@")"`.',
          option, option.name
        )

  def patch(self, parser):
    return Script(
      "{start}{guard_begin}\n{parser}{guard_end}\n{end}".format(
        start=self.contents[:self.guards.start],
        guard_begin=(
          "# docopt parser below, refresh this parser with `%s`"
          % parser.parameters.refresh_command_short),
        parser=parser.generate(self),
        guard_end=(
          "# docopt parser above, complete command for generating this parser is `%s`"
          % parser.parameters.refresh_command),
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
    self.offset = offset
    self.present = self.match is not None
    self.count = len(self.matches)
    self.start = self.match.start(0) + (self.offset or 0) if self.present else None  # type: ignore
    self.end = self.match.end(0) + (self.offset or 0) if self.present else None  # type: ignore
    self.line = self.script.contents[:self.start].count('\n') + 1
    self.all = [self] + [ScriptLocation(self.script, iter([match]), self.offset) for match in self.matches[1:]]
    if self.count == 0:
      self.last = None
    elif self.count == 1:
      self.last = self
    else:
      self.last = ScriptLocation(self.script, iter([self.matches[-1]]), self.offset)

  def __len__(self):
    return self.end - self.start if self.present else 0  # type: ignore

  def __str__(self):
    path = self.script.path if self.script.path is not None else 'STDIN'
    if not self.present:
      return '%s' % (path)
    if self.count > 1:
      return '%s:%s' % (path, ','.join(map(lambda loc: str(loc.line), self.all)))
    else:
      return '%s:%d' % (path, self.line)


class Doc(ScriptLocation):

  def __init__(self, script):
    # regex for quote matching yanked from:
    # https://www.metaltoad.com/blog/regex-quoted-string-escapable-quotes
    matches = re.finditer(
      r'^(?:[^#\n]*)'
      r'DOC='
      r'(?P<quote_start>(?<![\\])[\'"])'
      r'(?P<raw_value>'
      r'(?P<trimmed_before>\s*)'
      r'(?P<trimmed_raw_value>(?:.(?!(?<![\\])\1))*?.?)'
      r'(?P<trimmed_after>\s*))'
      r'(?P<quote_end>\1)(?:\n|;)',
      script.contents,
      re.MULTILINE | re.DOTALL
    )
    super(Doc, self).__init__(script, matches, 0)
    if self.present:
      # Get bash to output what the docstring looks like when evaluated
      output_doc = 'DOC={quote}{trimmed_raw_value}{quote};printf "%s" "$DOC"'.format(
        trimmed_raw_value=self.match.group('trimmed_raw_value'),  # type: ignore
        quote=self.match.group('quote_start')  # type: ignore
      )
      process = subprocess.run(
        ['bash', '-c', 'eval "$(cat)"'],
        input=output_doc.encode('utf-8'),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
      )
      if process.returncode != 0:
        raise DocoptScriptValidationError(
          self, 'Unable to evaluate DOC= with system bash: %s' % process.stderr.decode('utf-8')
        )
      self.trimmed_value = process.stdout.decode('utf-8')
      self.trimmed_value_start = self.match.start('trimmed_raw_value') - self.match.end('quote_start')  # type: ignore
      self.untrimmed_value = (
        self.match.group('trimmed_before')  # type: ignore
        + self.trimmed_value
        + self.match.group('trimmed_after')  # type: ignore
      )
    else:
      self.value = None


class TopGuard(ScriptLocation):

  def __init__(self, script):
    matches = re.finditer(
      r'# docopt parser below(, refresh this parser with `([^`]+)`)?.*\n',
      script.contents,
      re.MULTILINE
    )
    super(TopGuard, self).__init__(script, matches, 0)


class BottomGuard(ScriptLocation):

  def __init__(self, script, offset):
    matches = re.finditer(
      r'# docopt parser above(, complete command for generating this parser is `([^`]+)`)?.*\n',
      script.contents[offset:],
      re.MULTILINE
    )
    super(BottomGuard, self).__init__(script, matches, offset)
    self.refresh_command_params = None
    if self.present and self.match.group(2) is not None:  # type: ignore
      from .__main__ import __doc__
      try:
        self.refresh_command_params = docopt.docopt(__doc__, shlex.split(self.match.group(2))[1:])  # type: ignore
      except (docopt.DocoptLanguageError, docopt.DocoptExit):
        pass


class Guards(object):

  def __init__(self, script, doc):
    self.top = TopGuard(script)
    if self.top.present:
      self.bottom = BottomGuard(script, self.top.end)
    else:
      self.bottom = BottomGuard(script, 0)
    self.present = self.top.present and self.bottom.present
    # By defaulting start+end to doc.end the parser will be appended to
    # the doc if it is absent
    self.start = self.top.start if self.present else doc.end
    self.end = self.bottom.end if self.present else doc.end

  def __len__(self):
    return self.end - self.start if self.present else 0  # type: ignore


class Invocation(ScriptLocation):

  def __init__(self, script, parser):
    matches = re.finditer(r'eval "\$\(docopt\s+"\$\@"\)"', script.contents[parser.end:])
    super(Invocation, self).__init__(script, matches, parser.end)


class Option(ScriptLocation):

  def __init__(self, script, name):
    self.name = name
    matches = re.finditer(r'^%s=' % name, script.contents, re.MULTILINE)
    super(Option, self).__init__(script, matches, 0)
    if self.count > 1:
      # Override parent class selection of first match, previous assignments
      # would be overwritten so it's the last match that has an effect
      self.match = self.matches[-1]


class DocoptScriptValidationError(DocoptError):

  def __init__(self, message, script_location=None):
    # Exit code 74: input/output error (sysexits.h)
    super(DocoptScriptValidationError, self).__init__(message, exit_code=74)
    self.script_location = script_location

  def __str__(self):
    if self.script_location is not None:
      return '%s %s' % (self.script_location, self.message)
    return self.message
