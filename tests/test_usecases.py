import re
import shlex
import io
from packaging.version import parse as parse_version
from . import Usecase, patch_stream

bash_four_four = parse_version('4.4')


def test_usecase(monkeypatch, capsys, usecase, bash):
  assert convert_to_bash(bash, usecase) == run_usecase(monkeypatch, capsys, usecase, bash)


def run_usecase(monkeypatch, capsys, usecase, bash):
  file, lineno, _, doc, prog, argv, type, expect = usecase
  program_template = '''
DOC="{doc}"
"DOCOPT PARAMS"
eval "$(docopt "$@")"
if [[ -n ${{!_usecase_*}} ]]; then
  declare -p "${{!_usecase_@}}"
fi
'''
  program = program_template.format(doc=doc)
  run = patch_stream(
    monkeypatch, capsys,
    io.StringIO(program),
    docopt_params={'DOCOPT_PREFIX': '_usecase_'}
  )
  code, out, err = run(bash, *shlex.split(argv))
  if type == '>':
    result = {'code': code, 'stdout': out, 'stderr': err}
  elif code == 0:
    expr = re.compile('^declare (--|-a) ([^=]+)=')
    out = out.strip('\n')
    result = {}
    if err != '':
      result = 'Errors encountered while running usecase %s:%d: %s' % (file, lineno, err)
    else:
      if out != '':
        for line in out.split('\n'):
          if expr.match(line) is None:
            raise Exception('Unable to match output for usecase %s:%d: %s' % (file, lineno, line))
          result[expr.match(line).group(2)] = line  # type: ignore
  else:
    result = 'user-error'
  return Usecase(file, lineno, bash[0], doc, prog, argv, type, result)


def convert_to_bash(bash, usecase):
  file, lineno, _, doc, prog, argv, type, expect = usecase
  if type == '>' or expect == 'user-error':
    declarations = expect
  else:
    declarations = {}
    for key, value in expect.items():
      var = '_usecase_' + re.sub(r'^[^a-z_]|[^a-z0-9_]', '_', key, 0, re.IGNORECASE)
      declarations[var] = bash_decl(bash[0], var, value)
  return Usecase(file, lineno, bash[0], doc, prog, argv, type, declarations)


def bash_decl(bash_version, name, value):
  if value is None or type(value) in (bool, int, str):
    return 'declare -- {name}={value}'.format(name=name, value=bash_decl_value(bash_version, value))
  if type(value) is list:
    return 'declare -a {name}={value}'.format(name=name, value=bash_decl_value(bash_version, value))
  raise Exception('Unknown value type %s' % type(value))


def bash_decl_value(bash_version, value):
  if value is None:
    return '""'
  if type(value) is bool:
    return '"true"' if value else '"false"'
  if type(value) is int:
    return '"{value}"'.format(value=value)
  if type(value) is str:
    val = shlex.quote(value).strip("'")
    val = re.sub(r'(\$|")', r'\\\1', val)
    return '"{value}"'.format(value=val)
  if type(value) is list:
    list_tpl = "'({value})'"
    if bash_version >= bash_four_four:
      list_tpl = '({value})'
    return list_tpl.format(value=' '.join('[{i}]={value}'.format(
      i=i, value=bash_decl_value(bash_version, v)) for i, v in enumerate(value))
    )
