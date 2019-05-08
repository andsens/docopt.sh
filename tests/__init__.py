import subprocess
import shlex
from contextlib import contextmanager
import os
from docopt_sh.__main__ import main as docopt_sh_main

def bash_run_script(script, argv):
    argv = ' '.join(map(shlex.quote, argv))
    return subprocess.run(
        ['bash', '-c', 'set - %s; eval "$(cat)"' % argv],
        input=script.encode('utf-8'),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

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
        return '({value})'.format(value=' '.join('[{i}]={value}'.format(i=i, value=bash_decl_value(v)) for i, v in enumerate(value)))

def declare_quote(value):
    return value.replace('\\', '\\\\').replace('"', '\\"')

@contextmanager
def patched_script(monkeypatch, capsys, name):
    with monkeypatch.context() as m:
        with open(os.path.join('tests/scripts', name)) as script:
            def run(*argv):
                m.setattr('sys.stdin', script)
                docopt_sh_main()
                captured = capsys.readouterr()
                return bash_run_script(captured.out, argv)
            yield run
