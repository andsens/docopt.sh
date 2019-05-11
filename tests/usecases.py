import re
import json
import pytest
import subprocess
import shlex
from docopt_sh.script import Script
from docopt_sh.parser import Parser
from docopt_sh.bash import bash_variable_name
from . import bash_eval_script, bash_decl

import logging
log = logging.getLogger(__name__)


class DocoptUsecaseTestFile(pytest.File):

  def collect(self):
    raw = self.fspath.open().read()
    index = 1
    params = {
      'SCRIPT': None,
      '--prefix': '_',
      '--options-first': False,
      '--no-help': False,
      '--no-version': False,
      '--no-doc-check': True,
      '--no-teardown': True,
      '--no-minimize': False,
      '--line-length': '80',
      '--debug': False,
    }
    program_template = '''
doc="{doc}"
docopt "$@"
for var in "${{param_names[@]}}"; do declare -p "$var"; done
'''
    for name, doc, cases in self._parse_test(raw):
      name = self.fspath.purebasename
      if cases:
        script = Script(program_template.format(doc=doc))
        parser = Parser(script, params)
        script = str(parser.patched_script)
      for bash in self.config.bash_versions:
        for case in cases:
          yield DocoptUsecaseTest("%s (%d, bash %s)" % (name, index, bash[0]), self, bash, doc, script, case)
          index += 1

  def _parse_test(self, raw):
    raw = re.compile('#.*$', re.M).sub('', raw).strip()
    if raw.startswith('"""'):
      raw = raw[3:]

    for fixture in raw.split('r"""'):
      name = ''
      doc, _, body = fixture.partition('"""')
      cases = []
      for case in body.split('$')[1:]:
        argv, _, expect = case.strip().partition('\n')
        expect = json.loads(expect)
        prog, _, argv = argv.strip().partition(' ')
        cases.append((prog, argv, expect))

      yield name, doc, cases


class DocoptUsecaseTest(pytest.Item):

  def __init__(self, name, parent, bash, doc, script, case):
    super(DocoptUsecaseTest, self).__init__(name, parent)
    self.doc = doc
    self.script = script
    self.prog, self.argv, self.expect = case
    self.bash = bash
    if type(self.expect) is dict:
      self.expect = {
        bash_variable_name(k, prefix='_'): bash_decl(
          bash_variable_name(k, prefix='_'), v, bash_version=self.bash[0]
        )
        for k, v in self.expect.items()
      }

  def runtest(self):
    try:
      code, out, err = bash_eval_script(self.script, shlex.split(self.argv), bash=self.bash)
      if code == 0:
        expr = re.compile('^declare (--|-a) ([^=]+)=')
        out = out.strip('\n')
        result = {}
        if out != '':
          result = {expr.match(line).group(2): line for line in out.split('\n')}
      else:
        result = 'user-error'
    except Exception as e:
      log.exception(e)

    if self.expect != result:
      if len(err) > 0:
        log.error(self.doc)
        log.error(err)
      raise DocoptUsecaseTestException(self, result)

  def repr_failure(self, excinfo):
    """Called when self.runtest() raises an exception."""
    if isinstance(excinfo.value, DocoptUsecaseTestException):
      return "\n".join((
        "usecase execution failed:",
        self.doc.rstrip(),
        "$ %s %s" % (self.prog, self.argv),
        "result> %s" % json.dumps(excinfo.value.args[1]),
        "expect> %s" % json.dumps(self.expect),
      ))

  def reportinfo(self):
    return self.fspath, 0, "usecase: %s" % self.name


class DocoptUsecaseTestException(Exception):
  pass
