import json
from docopt_sh.__main__ import main as docopt_sh_main
from tempfile import NamedTemporaryFile
from . import bash_run_script

def test_stdin(monkeypatch, capsys):
    with monkeypatch.context() as m:
        with open('tests/scripts/echo_ship_name.sh') as script:
            m.setattr('sys.stdin', script)
            docopt_sh_main()
            captured = capsys.readouterr()
            process = bash_run_script(captured.out, ['ship', 'new', 'Britannica'])
            process.check_returncode()
            assert process.stdout.decode('utf-8') == 'Britannica\n'
