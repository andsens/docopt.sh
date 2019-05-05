import re
try:
    import json
except ImportError:
    import simplejson as json

import pytest

import subprocess

import shlex

from parser import parse_doc
from generator import generate_parser,generate_invocation,bash_name

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
                expect = {bash_name(k): bash_decl(bash_name(k), v) for k, v in expect.items()}
            prog, _, argv = argv.strip().partition(' ')
            cases.append((prog, argv, expect))

        yield name, doc, cases


class DocoptTestFile(pytest.File):

    def collect(self):
        raw = self.fspath.open().read()
        index = 1

        for name, doc, cases in parse_test(raw):
            name = self.fspath.purebasename
            if cases:
                pattern = parse_doc(doc)
                parser = generate_parser(pattern, 'doc')
                parser += generate_invocation()
            for case in cases:
                yield DocoptTestItem("%s(%d)" % (name, index), self, doc, parser, case)
                index += 1


class DocoptTestItem(pytest.Item):

    def __init__(self, name, parent, doc, parser, case):
        super(DocoptTestItem, self).__init__(name, parent)
        self.doc = doc
        self.parser = parser
        self.prog, self.argv, self.expect = case

    def runtest(self):
        program = 'doc="%s"\n%s' % (self.doc, self.parser)
        try:
            process = subprocess.run(
                ['./output-parsed.sh'] + shlex.split(self.argv),
                input=program.encode('utf-8'),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            process.check_returncode()
            expr = re.compile('^declare (--|-a) ([^=]+)=')
            out = process.stdout.decode('utf-8').strip('\n')
            result = {}
            if out != '':
                result = {expr.match(line).group(2): line for line in out.split('\n')}
        except subprocess.CalledProcessError as e:
            result = 'user-error'
        except Exception as e:
            log.error(self.doc)
            log.error(process.stdout.decode('utf-8'))
            log.exception(e)

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


def bash_decl(name, value):
    if value is None or type(value) in (bool, int, str):
        return 'declare -- {name}={value}'.format(name=name, value=bash_decl_value(value))
    if type(value) is list:
        return 'declare -a {name}={value}'.format(name=name, value=bash_decl_value(value))
    raise Exception('Unknown value type %s' % type(value))

def bash_decl_value(value):
    if value is None:
        return '""'
    if type(value) is bool:
        return '"true"' if value else '"false"'
    if type(value) is int:
        return '"{value}"'.format(value=value)
    if type(value) is str:
        return '"{value}"'.format(value=shlex.quote(value).strip("'"))
    if type(value) is list:
        return '({value})'.format(value=' '.join('[{i}]={value}'.format(i=i, value=bash_decl_value(v)) for i, v in enumerate(value)))

def declare_quote(value):
    return value.replace('\\', '\\\\').replace('"', '\\"')
