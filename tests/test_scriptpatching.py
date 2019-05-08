from . import patched_script

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
