import os
import sys
from . import patched_script, invoke_docopt, temp_script

def test_arg(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    code, out, err = run('ship', 'new', 'Britannica')
    assert code == 0
    assert out == 'Britannica\n'

def test_version(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    code, out, err = run('--version')
    assert code == 0
    assert out == '0.1.5\n'

def test_help(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    code, out, err = run('--help')
    assert code == 0
    assert out == 'Usage: naval_fate.py ship new <name>...\n'

def test_wrong_usage(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    code, out, err = run('--bad-opt')
    assert code != 0

def test_no_version(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh', ['--no-version']) as run:
    code, out, err = run('--version')
    assert out == 'Usage: naval_fate.py ship new <name>...\n'

def test_patch_file(monkeypatch):
  with temp_script('echo_ship_name.sh') as (script, run):
    invoke_docopt(monkeypatch, params=[script.name])
    code, out, err = run(['ship', 'new', 'Olympia'])
    assert out == 'Olympia\n'
