import re
from io import StringIO
from . import bash_eval_script, patched_script, invoke_docopt, temp_script
from docopt_sh.patcher import get_doc

def test_arg(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    code, out, err = run('ship', 'new', 'Britannica')
    assert code == 0
    assert out == 'Britannica\n'

def test_wrong_usage(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    code, out, err = run('--bad-opt')
    assert code != 0

def test_help(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    code, out, err = run('--help')
    assert code == 0
    assert out == 'Usage: echo_ship_name.sh ship new <name>...\n'

def test_no_help(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh', ['--no-help']) as run:
    code, out, err = run('--help')
    assert code == 1
    assert out == 'Usage: echo_ship_name.sh ship new <name>...\n'

def test_version(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh') as run:
    code, out, err = run('--version')
    assert code == 0
    assert out == '0.1.5\n'

def test_no_version(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'echo_ship_name.sh', ['--no-version']) as run:
    code, out, err = run('--version')
    assert out == 'Usage: echo_ship_name.sh ship new <name>...\n'

def test_options_anywhere(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'naval_fate.sh') as run:
    code, out, err = run('ship', 'Titanic', 'move', '1', '--speed', '6', '4')
    assert out == 'The Titanic is now moving to 1,4 at 6 knots.\n'

def test_options_first(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'naval_fate.sh', ['--options-first']) as run:
    code, out, err = run('--speed', '6', 'ship', 'Titanic', 'move', '1', '4')
    assert code == 0
    assert out == 'The Titanic is now moving to 1,4 at 6 knots.\n'

def test_options_first_fail(monkeypatch, capsys):
  with patched_script(monkeypatch, capsys, 'naval_fate.sh', ['--options-first']) as run:
    code, out, err = run('ship', 'Titanic', 'move', '1', '--speed', '6', '4')
    assert code == 1
    assert out.startswith('Naval Fate.')

def test_patch_file(monkeypatch):
  with temp_script('echo_ship_name.sh') as (script, run):
    invoke_docopt(monkeypatch, params=[script.name])
    code, out, err = run(['ship', 'new', 'Olympia'])
    assert out == 'Olympia\n'

def test_doc_check(monkeypatch):
  with temp_script('echo_ship_name.sh') as (script, run):
    invoke_docopt(monkeypatch, params=[script.name])
    with open(script.name, 'r') as h:
      contents = h.read()
    contents = contents.replace('ship new <name>', 'ship delete <name>')
    with open(script.name, 'w') as h:
      h.write(contents)
    code, out, err = run(['ship', 'new', 'Olympia'])
    assert re.match('^The current usage doc \([^)]+\) does not match what the parser was generated with \([^)]+\)\n$', err) is not None

def test_no_doc_check(monkeypatch):
  with temp_script('echo_ship_name.sh') as (script, run):
    invoke_docopt(monkeypatch, params=['--no-doc-check', script.name])
    with open(script.name, 'r') as h:
      contents = h.read()
    contents = contents.replace('ship new <name>', 'ship delete <name>')
    with open(script.name, 'w') as h:
      h.write(contents)
    code, out, err = run(['ship', 'new', 'Olympia'])
    assert out == 'Olympia\n'

def test_only_parser(monkeypatch, capsys):
  with open('tests/scripts/naval_fate.sh') as h:
    script = h.read()
  doc = get_doc(script)[0]
  parser = invoke_docopt(monkeypatch, capsys=capsys, params=['--only-parser'], stdin=StringIO(script)).out
  program = '''
doc="{doc}"
{parser}
docopt "$@"
echo $((__x_ + __y_))
'''.format(doc=doc, parser=parser)
  captured = invoke_docopt(monkeypatch, capsys, stdin=StringIO(program))
  code, out, err = bash_eval_script(captured.out, ['ship', 'shoot', '3', '1'])
  assert code == 0
  assert out == '4\n'

def test_teardown(monkeypatch, capsys):
  with open('tests/scripts/naval_fate.sh') as h:
    doc = get_doc(h.read())[0]
  program = '''
doc="{doc}"
docopt "$@"
echo ${{parsed_params[0]}}
echo ${{parsed_values[0]}}
'''.format(doc=doc)
  program = invoke_docopt(monkeypatch, capsys=capsys, stdin=StringIO(program)).out
  code, out, err = bash_eval_script(program, ['ship', 'shoot', '3', '1'])
  assert err == ''
  assert code == 0
  assert out == '\n\n'

def test_no_teardown(monkeypatch, capsys):
  with open('tests/scripts/naval_fate.sh') as h:
    doc = get_doc(h.read())[0]
  program = '''
doc="{doc}"
docopt "$@"
echo ${{parsed_params[@]}}
echo ${{parsed_values[@]}}
'''.format(doc=doc)
  program = invoke_docopt(monkeypatch, capsys=capsys, params=['--no-teardown'], stdin=StringIO(program)).out
  code, out, err = bash_eval_script(program, ['ship', 'shoot', '3', '1'])
  assert code == 0
  assert out == 'a a a a\nship shoot 3 1\n'
