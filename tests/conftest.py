import logging
import os
import urllib.request
import tarfile
import subprocess
import re
import glob
from .usecases import DocoptUsecaseTestFile

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
    all_versions = [version for version, _ in session.config.bash_versions]
    log.warning('Testing with bash versions: %s' % ', '.join(all_versions))
  elif bash_version:
    session.config.bash_versions = [get_bash_version(version) for version in bash_version.split(',')]
    log.warning('Testing with bash versions: %s' % ', '.join(bash_version.split(',')))
  else:
    version, executable = get_system_bash()
    log.warning('Testing with system bash: %s' % version)
    session.config.bash_versions = [(version, executable)]


def pytest_collect_file(path, parent):
  if path.basename == 'usecases.txt':
    return DocoptUsecaseTestFile(path, parent)


def pytest_generate_tests(metafunc):
  if 'bash' in metafunc.fixturenames:
    if metafunc.config.bash_versions:
      metafunc.parametrize('bash', metafunc.config.bash_versions)


def get_system_bash():
  process = subprocess.run(
    ['bash', '--version'],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
  )
  process.check_returncode()
  out = process.stdout.decode('utf-8')
  match = re.search(r'GNU bash, version ([^ ]+)', out)
  if not match:
    log.warning('Unable to detect installed bash version from:\n%s\nAssuming 4.4' % out)
    return '4.4', 'bash'
  else:
    return match.group(1), 'bash'


def get_installed_bash_versions():
  versions = [get_system_bash()]
  for executable in glob.glob('tests/bash-versions/bash-*/bash'):
    folder_name = os.path.basename(os.path.dirname(executable))
    versions.append((re.search(r'bash-(.+)', folder_name).group(1), executable))
  return versions


def get_bash_version(version):
  versions_path = 'tests/bash-versions'
  if not os.path.exists(versions_path):
    os.mkdir(versions_path)
  version_path = os.path.join(versions_path, 'bash-%s' % version)
  executable_path = os.path.join(version_path, 'bash')
  if not os.path.exists(executable_path):
    log.warning('bash-%s executable not found in tests/bash-versions, downloading & compiling now' % version)
    archive_path = os.path.join(versions_path, 'bash-%s.tar.gz' % version)
    if os.path.exists(archive_path):
      log.warning('%s already exists, skipping download' % archive_path)
    else:
      url = 'http://ftp.gnu.org/gnu/bash/bash-%s.tar.gz' % version
      urllib.request.urlretrieve(url, archive_path)
    if os.path.exists(version_path):
      log.warning('%s already exists, skipping extraction' % version_path)
    else:
      with tarfile.open(archive_path) as archive:
        archive.extractall(versions_path)
    makefile_path = os.path.join(version_path, 'Makefile')
    if os.path.exists(makefile_path):
      log.warning('%s already exists, skipping ./configure' % makefile_path)
    else:
      process = subprocess.run('./configure', cwd=version_path)
      process.check_returncode()
    process = subprocess.run('make', cwd=version_path)
    process.check_returncode()
  return version, executable_path
