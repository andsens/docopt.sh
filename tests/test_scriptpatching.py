import json
from . import patched_script

def test_stdin(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    process = run('ship', 'new', 'Britannica')
    process.check_returncode()
    assert process.stdout.decode('utf-8') == 'Britannica\n'
