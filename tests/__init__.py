import subprocess
import shlex
import os
import io
from tempfile import NamedTemporaryFile
from collections import namedtuple
from contextlib import contextmanager
from docopt_sh.__main__ import main as docopt_sh_main
from docopt_sh.bash import bash_variable_value

Usecase = namedtuple('Usecase', ['file', 'line', 'bash', 'doc', 'prog', 'argv', 'expect'])


def bash_eval_script(bash, script, argv):
  argv = ' '.join(map(shlex.quote, argv))
  process = subprocess.run(
    [bash[1], '-c', 'set - %s; eval "$(cat)"' % argv],
    input=script.encode('utf-8'),
    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    timeout=2
  )
  return process.returncode, process.stdout.decode('utf-8'), process.stderr.decode('utf-8')


def declare_quote(value):
  return value.replace('\\', '\\\\').replace('"', '\\"')


def replace_docopt_params(stream, docopt_params):
  script = stream.read()
  params = '\n'.join([k + '=' + bash_variable_value(v) for k, v in docopt_params.items()])
  script = script.replace('"DOCOPT PARAMS"', params)
  return io.StringIO(script)


def patch_stream(monkeypatch, capsys, stream, program_params=[], docopt_params={}):
  stream = replace_docopt_params(stream, docopt_params)
  captured = invoke_docopt(monkeypatch, capsys, stdin=stream, program_params=program_params + ['-'])

  def run(bash, *argv):
    return bash_eval_script(bash, captured.out, argv)
  return run


def patch_file(monkeypatch, capsys, name, program_params=[], docopt_params={}):
  with open(os.path.join('tests/scripts', name)) as handle:
    return patch_stream(monkeypatch, capsys, handle, program_params, docopt_params)


@contextmanager
def temp_file(name, docopt_params={}):
  with open(os.path.join('tests/scripts', name)) as handle:
    script = replace_docopt_params(handle, docopt_params).read()
  file = NamedTemporaryFile(mode='w', delete=False)
  try:
    file.write(script)
    file.close()

    def run(bash, *args):
      process = subprocess.run(
        [bash[1], file.name] + list(args),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
      )
      return process.returncode, process.stdout.decode('utf-8'), process.stderr.decode('utf-8')
    yield file, run
  finally:
    os.unlink(file.name)


@contextmanager
def generated_library(monkeypatch, capsys, program_params=[]):
  file = NamedTemporaryFile(mode='w', delete=False)
  try:
    captured = invoke_docopt(monkeypatch, capsys, program_params=['generate-library'] + program_params)
    file.write(captured.out)
    file.close()
    yield file
  finally:
    os.unlink(file.name)


def invoke_docopt(monkeypatch, capsys=None, program_params=[], stdin=None):
  with monkeypatch.context() as m:
    if stdin is not None:
      m.setattr('sys.stdin', stdin)
    m.setattr('sys.argv', ['docopt.sh'] + program_params)
    docopt_sh_main()
    if capsys is not None:
      return capsys.readouterr()
    return None
