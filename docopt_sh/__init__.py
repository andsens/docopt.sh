"""
docopt.sh - Bash argument parser generator.
  This program looks for `DOC="... Usage​: ..."`  in a script
  and appends a matching parser to it.
"""
# The "... Usage: ..." above contains a zero-width space between `Usage` and `:`
# in order to prevent docopt from parsing it as a `usage:`` section
import importlib.metadata

try:
  __version__ = importlib.metadata.version('docopt-sh')
except importlib.metadata.PackageNotFoundError:
  __version__ = '0.0.0-dev'


class DocoptError(Exception):
  def __init__(self, message, exit_code=1):
    self.message = message
    self.exit_code = exit_code
