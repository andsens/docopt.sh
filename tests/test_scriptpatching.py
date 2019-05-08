import os
import sys
import subprocess
from tempfile import NamedTemporaryFile
from . import patched_script
from docopt_sh.__main__ import main as docopt_sh_main

def test_arg(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    process = run('ship', 'new', 'Britannica')
    process.check_returncode()
    assert process.stdout.decode('utf-8') == 'Britannica\n'

def test_version(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    process = run('--version')
    process.check_returncode()
    assert process.stdout.decode('utf-8') == '0.1.5\n'

def test_help(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    process = run('--help')
    process.check_returncode()
    assert process.stdout.decode('utf-8') == 'Usage: naval_fate.py ship new <name>...\n'

def test_wrong_usage(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    process = run('--bad-opt')
    assert process.returncode != 0

def test_no_version(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh', ['--no-version']) as run:
    process = run('--version')
    assert process.stdout.decode('utf-8') == 'Usage: naval_fate.py ship new <name>...\n'

def test_patch_file(monkeypatch):
  with open('tests/scripts/echo_ship_name.sh') as h:
    script = h.read()
  file = NamedTemporaryFile(mode='w', delete=False)
  try:
    file.write(script)
    file.close()
    with monkeypatch.context() as m:
      m.setattr(sys, 'argv', ['docopt.sh', file.name])
      docopt_sh_main()
      process = subprocess.run(
        ['bash', file.name, 'ship', 'new', 'Olympia'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
      )
      assert process.stdout.decode('utf-8') == 'Olympia\n'
  finally:
    os.unlink(file.name)
