import subprocess
import shlex
from tempfile import NamedTemporaryFile
import os
from contextlib import contextmanager
from docopt_sh.__main__ import main as docopt_sh_main


def bash_eval_script(script, argv):
  argv = ' '.join(map(shlex.quote, argv))
  process = subprocess.run(
    ['bash', '-c', 'set - %s; eval "$(cat)"' % argv],
    input=script.encode('utf-8'),
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
  )
  return process.returncode, process.stdout.decode('utf-8'), process.stderr.decode('utf-8')


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
    return '({value})'.format(value=' '.join('[{i}]={value}'.format(
      i=i, value=bash_decl_value(v)) for i, v in enumerate(value))
    )


def declare_quote(value):
  return value.replace('\\', '\\\\').replace('"', '\\"')


@contextmanager
def patched_script(monkeypatch, capsys, name, docopt_params=[]):
  with monkeypatch.context() as m:
    with open(os.path.join('tests/scripts', name)) as script:
      def run(*argv):
        captured = invoke_docopt(m, capsys, stdin=script, params=docopt_params)
        return bash_eval_script(captured.out, argv)
      yield run


@contextmanager
def temp_script(name):
  with open(os.path.join('tests/scripts', name)) as h:
    script = h.read()
  file = NamedTemporaryFile(mode='w', delete=False)
  try:
    file.write(script)
    file.close()

    def run(args):
      process = subprocess.run(
        ['bash', file.name] + args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
      )
      return process.returncode, process.stdout.decode('utf-8'), process.stderr.decode('utf-8')
    yield file, run
  finally:
    os.unlink(file.name)


def invoke_docopt(monkeypatch, capsys=None, params=[], stdin=None):
  with monkeypatch.context() as m:
    if stdin is not None:
      m.setattr('sys.stdin', stdin)
    m.setattr('sys.argv', ['docopt.sh'] + params)
    docopt_sh_main()
    if capsys is not None:
      return capsys.readouterr()
    return None
