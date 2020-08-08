#!/usr/bin/env python3
"""
Downloads, extracts, configures, and compiles bash versions for testing
Usage:
  get_bash.py VERSION...
"""

import os
import logging
import urllib.request
import tarfile
import subprocess
import docopt

log = logging.getLogger('get_bash.py')
logging.basicConfig(level=logging.INFO)


def get_bash(version):
  try:
    versions_path = os.path.join(os.path.dirname(__file__), 'bash-versions')
    if not os.path.exists(versions_path):
      os.mkdir(versions_path)
    version_path = os.path.join(versions_path, 'bash-%s' % version)
    executable_path = os.path.join(version_path, 'bash')
    if not os.path.exists(executable_path):
      log.info('bash-%s executable not found in tests/bash-versions, downloading & compiling now' % version)
      archive_path = os.path.join(versions_path, 'bash-%s.tar.gz' % version)
      if os.path.exists(archive_path):
        log.info('%s already exists, skipping download' % archive_path)
      else:
        url = 'http://ftp.gnu.org/gnu/bash/bash-%s.tar.gz' % version
        urllib.request.urlretrieve(url, archive_path)
      if os.path.exists(version_path):
        log.info('%s already exists, skipping extraction' % version_path)
      else:
        with tarfile.open(archive_path) as archive:
          archive.extractall(versions_path)
      makefile_path = os.path.join(version_path, 'Makefile')
      if os.path.exists(makefile_path):
        log.info('%s already exists, skipping ./configure' % makefile_path)
      else:
        process = subprocess.run('./configure', cwd=version_path)
        process.check_returncode()
      process = subprocess.run('make', cwd=version_path)
      process.check_returncode()
    else:
      log.info('bash-%s is already installed' % version)
  except subprocess.CalledProcessError:
    log.error('Failed to install bash-%s' % version)
    raise


if __name__ == '__main__':
  params = docopt.docopt(__doc__)
  versions = params['VERSION']
  if len(versions) == 1 and ',' in versions:
    versions = versions[0].split(',')
  for version in versions:
    get_bash(version)
