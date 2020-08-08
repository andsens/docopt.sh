import logging
import os
import subprocess
import re
import glob
import json
import itertools
from packaging.version import parse as parse_version
from . import Usecase

log = logging.getLogger(__name__)


def pytest_addoption(parser):
  parser.addoption(
    '--bash-version', type=str,
    help='test with specific bash version (comma separated, or "all" for all installed versions)'
  )


def pytest_sessionstart(session):
  bash_version = session.config.getoption('--bash-version')
  if bash_version == 'all':
    session.config.bash_versions = get_installed_bash_versions()
    all_versions = sorted([version for version, _ in session.config.bash_versions])
    log.info('Testing with bash versions: %s' % ', '.join(map(str, all_versions)))
  elif bash_version:
    selected_versions = [get_bash_version(version) for version in bash_version.split(',')]
    session.config.bash_versions = selected_versions
    log.info('Testing with bash versions: %s' % ', '.join(map(str, selected_versions)))
  else:
    version, executable = get_system_bash()
    log.info('Testing with system bash: %s' % version)
    session.config.bash_versions = [(version, executable)]


def pytest_generate_tests(metafunc):
  if 'bash' in metafunc.fixturenames:
    if metafunc.config.bash_versions:
      metafunc.parametrize(
        'bash',
        metafunc.config.bash_versions,
        ids=map(lambda v: str(v[0]), metafunc.config.bash_versions)
      )
  if 'usecase' in metafunc.fixturenames:
    usecase_generators = []
    for path in glob.glob(os.path.join(os.path.dirname(__file__), '*-usecases.txt')):
      usecase_generators.append(parse_usecases(path))
    cases, copied_cases = itertools.tee(itertools.chain(*usecase_generators))
    ids = ('%s:%d' % (case.file, case.line) for case in copied_cases)
    metafunc.parametrize('usecase', cases, ids=ids)


def pytest_assertrepr_compare(config, op, left, right):
  if isinstance(left, Usecase) and isinstance(right, Usecase) and op == '==':
    error = ['Usecase in %s:%d failed' % (left.file, left.line)]
    error.append('bash: %s' % left.bash)
    error.append('%s' % left.doc)
    error.append('$ %s %s' % (left.prog, left.argv))
    if isinstance(left.expect, str) or isinstance(right.expect, str):
      error.append('%s != %s' % (repr(left.expect), repr(right.expect)))
    else:
      for key, value in left.expect.items():
        if key in right.expect:
          if value != right.expect[key]:
            error.append('%s != %s' % (repr(value), repr(right.expect[key])))
        else:
          error.append('%s != (key %s not found)' % (repr(value), key))
      for key, value in right.expect.items():
        if key not in left.expect:
          error.append('(key %s not found) != %s' % (key, repr(value)))
    return error


def parse_usecases(path):
  with open(path, 'r') as handle:
    raw = handle.read()
  fixture_pattern = re.compile(r'r"""(?P<doc>.+?)""".*?(?=r"""|$(?!.))', re.DOTALL)
  case_pattern = re.compile(
    r'\$ (?P<prog>[^\n ]+)( (?P<argv>[^\n]+))?\n(?P<expect>(\n|.)+?)(?P<comment>\s*#[^\n]*)?\n(\n|$(?!.))')
  for fixture_match in fixture_pattern.finditer(raw):
    line_offset = raw[:fixture_match.start(0)].count('\n') + 1
    fixture = fixture_match.group(0)
    doc = fixture_match.group('doc')
    for case_match in case_pattern.finditer(fixture):
      file = os.path.basename(path)
      line = line_offset + fixture[:case_match.start(0)].count('\n')
      case = case_match.group(0)
      prog = case_match.group('prog')
      argv = case_match.group('argv')
      argv = argv if argv else ''
      try:
        expect = json.loads(case_match.group('expect'))
      except json.decoder.JSONDecodeError as e:
        json_line = line_offset + fixture[:case_match.start('expect')].count('\n')
        raise Exception('Error on line %d:\n%s\n---\n%s' % (json_line, case, str(e)))
      yield Usecase(file, line, None, doc, prog, argv, expect)


def get_system_bash():
  process = subprocess.run(
    ['bash', '--version'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
  )
  process.check_returncode()
  out = process.stdout.decode('utf-8')
  match = re.search(r'GNU bash, version (\d+\.\d+\.\d+)', out)
  if not match:
    raise Exception('Unable to detect installed bash version from: %s' % out)
  else:
    return parse_version(match.group(1)), 'bash'


def get_installed_bash_versions():
  versions = [get_system_bash()]
  for executable in glob.glob('tests/bash-versions/bash-*/bash'):
    folder_name = os.path.basename(os.path.dirname(executable))
    versions.append((parse_version(re.search(r'bash-(.+)', folder_name).group(1)), executable))
  return versions


def get_bash_version(version):
  executable_path = os.path.join(os.path.dirname(__file__), 'bash-versions/bash-%s/bash' % version)
  if not os.path.exists(executable_path):
    raise Exception(
      'bash-{version} is not installed. '
      'Use `tests/get_bash.py {version}` to do that'
      .format(version=version)
    )
  return parse_version(version), executable_path
