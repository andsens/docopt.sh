import re
try:
    import json
except ImportError:
    import simplejson as json

import pytest

import subprocess

import shlex

from docopt_sh import bash_name, bash_value

import logging
log = logging.getLogger(__name__)

def pytest_collect_file(path, parent):
    if path.ext == ".docopt" and path.basename.startswith("test"):
        return DocoptTestFile(path, parent)


def parse_test(raw):
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
                expect = {bash_name(k): bash_value(v) for k, v in expect.items()}
            prog, _, argv = argv.strip().partition(' ')
            cases.append((prog, argv, expect))

        yield name, doc, cases


class DocoptTestFile(pytest.File):

    def collect(self):
        raw = self.fspath.open().read()
        index = 1

        for name, doc, cases in parse_test(raw):
            name = self.fspath.purebasename
            for case in cases:
                yield DocoptTestItem("%s(%d)" % (name, index), self, doc, case)
                index += 1


class DocoptTestItem(pytest.Item):

    def __init__(self, name, parent, doc, case):
        super(DocoptTestItem, self).__init__(name, parent)
        self.doc = doc
        self.prog, self.argv, self.expect = case

    def runtest(self):
        try:
            process = subprocess.run(['./test.sh', '-'] + shlex.split(self.argv), input=self.doc.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.check_returncode()
            result = {}
            for line in process.stdout.decode('utf-8').strip('\n').split('\n'):
                keyval = line.split(': ', maxsplit=1)
                result[str(keyval[0])] = keyval[1] if len(keyval) == 2 else ''
        except subprocess.CalledProcessError as e:
            result = 'user-error'

        if self.expect != result:
            if(len(process.stderr)):
                log.error(process.stderr.decode('utf-8'))
            raise DocoptTestException(self, result)

    def repr_failure(self, excinfo):
        """Called when self.runtest() raises an exception."""
        if isinstance(excinfo.value, DocoptTestException):
            return "\n".join((
                "usecase execution failed:",
                self.doc.rstrip(),
                "$ %s %s" % (self.prog, self.argv),
                "result> %s" % json.dumps(excinfo.value.args[1]),
                "expect> %s" % json.dumps(self.expect),
            ))

    def reportinfo(self):
        return self.fspath, 0, "usecase: %s" % self.name


class DocoptTestException(Exception):
    pass
