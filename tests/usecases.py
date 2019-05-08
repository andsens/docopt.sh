import re
import json
import pytest
import subprocess
import shlex
from docopt_sh.parser import parse_doc
from docopt_sh.generator import generate_parser,bash_name
from . import bash_run_script,bash_decl,bash_decl_value,declare_quote

import logging
log = logging.getLogger(__name__)


class DocoptUsecaseTestFile(pytest.File):

  def collect(self):
    raw = self.fspath.open().read()
    index = 1

    for name, doc, cases in self._parse_test(raw):
      name = self.fspath.purebasename
      if cases:
        pattern = parse_doc(doc)
        parser = generate_parser(pattern, 'doc')
      for case in cases:
        yield DocoptUsecaseTest("%s(%d)" % (name, index), self, doc, parser, case)
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
        if type(expect) is dict:
          expect = {bash_name(k): bash_decl(bash_name(k), v) for k, v in expect.items()}
        prog, _, argv = argv.strip().partition(' ')
        cases.append((prog, argv, expect))

      yield name, doc, cases


class DocoptUsecaseTest(pytest.Item):

  def __init__(self, name, parent, doc, parser, case):
    super(DocoptUsecaseTest, self).__init__(name, parent)
    self.doc = doc
    self.parser = parser
    self.prog, self.argv, self.expect = case

  def runtest(self):
    program = '''
doc="{doc}"
{parser}
docopt "$@"
for var in "${{param_names[@]}}"; do declare -p "$var"; done
'''.format(doc=self.doc, parser=self.parser)
    try:
      process = bash_run_script(program, shlex.split(self.argv))
      process.check_returncode()
      expr = re.compile('^declare (--|-a) ([^=]+)=')
      out = process.stdout.decode('utf-8').strip('\n')
      result = {}
      if out != '':
        result = {expr.match(line).group(2): line for line in out.split('\n')}
    except subprocess.CalledProcessError as e:
      result = 'user-error'
    except Exception as e:
      log.exception(e)

    if self.expect != result:
      if(len(process.stderr)):
        log.error(self.doc)
        log.error(process.stderr.decode('utf-8'))
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

