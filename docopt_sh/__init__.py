"""
docopt.sh - Bash argument parser generator.
  This program looks for `DOC="... Usage​: ..."`  in a script
  and appends a matching parser to it.
"""
# The "... Usage: ..." above contains a zero-width space between `Usage` and `:`
# in order to prevent docopt from parsing it as a `usage:`` section

__all__ = ['docopt_sh']
try:
  from importlib import metadata
except ImportError:
  import importlib_metadata as metadata
try:
  __version__ = metadata.version(__name__)
except Exception as e:
  from os import getenv
  __version__ = getenv('DOCOPT_SH_VERSION', None)
  if __version__ is None:
    raise e


class DocoptError(Exception):
  def __init__(self, message, exit_code=1):
    self.message = message
    self.exit_code = exit_code
