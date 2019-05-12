import hashlib
from .. import Function, bash_ifs_value
from ...doc import Option


class Main(Function):
  def __init__(self, settings, root_node, leaf_nodes):
    super(Main, self).__init__(settings, 'docopt')
    self.root_node = root_node
    self.leaf_nodes = leaf_nodes

  @property
  def body(self):
    body = ''
    if self.settings.add_doc_check:
      body += '''
local doc_hash
local digest="{digest}"
doc_hash=$(printf "%s" "${docname}" | shasum -a 256)
if [[ ${{doc_hash:0:5}} != "$digest" ]]; then
  printf "The current usage doc (%s) does not match what the parser was generated with (%s)\\n" \\
    "$doc_hash" "$digest" >&2
  exit 70
fi
'''.format(
        docname=self.settings.script.doc.name,
        digest=hashlib.sha256(self.settings.script.doc.value.encode('utf-8')).hexdigest()[0:5]
      )
    # variables setup
    option_nodes = [o for o in self.leaf_nodes if o.type is Option]
    body += '''
_do_av=("$@")
_do_sh=({options_short})
_do_lo=({options_long})
_do_ac=({options_argcount})
_do_pn=({param_names})
_do_pp=()
_do_pv=()
_lft=()
_do_tm=false
local var
for var in "${{_do_pn[@]}}"; do
  unset "$var"
done
'''.format(
      options_short=' '.join([bash_ifs_value(o.pattern.short) for o in option_nodes]),
      options_long=' '.join([bash_ifs_value(o.pattern.long) for o in option_nodes]),
      options_argcount=' '.join([bash_ifs_value(o.pattern.argcount) for o in option_nodes]),
      param_names=' '.join([node.variable_name for node in self.leaf_nodes]),
    )
    # parse _do_av
    body += '''
local arg
while [[ ${#_do_av[@]} -gt 0 ]]; do
  if [[ ${_do_av[0]} = "--" ]]; then
    for arg in "${_do_av[@]}"; do
      _do_pp+=('a')
      _do_pv+=("$arg")
    done
    break
  elif [[ ${_do_av[0]} = --* ]]; then
    _do_long
  elif [[ ${_do_av[0]} = -* && ${_do_av[0]} != "-" ]]; then
    _do_shorts
  else
'''
    if self.settings.options_first:
      body += '''
    for arg in "${_do_av[@]}"; do
      _do_pp+=('a')
      _do_pv+=("$arg")
    done
    break
'''
    else:
      body += '''
    _do_pp+=('a')
    _do_pv+=("${_do_av[0]}")
    _do_av=("${_do_av[@]:1}")
'''
    body += '''
  fi
done
'''

    # extras
    if self.settings.add_help or self.settings.add_version:
      body += 'local idx'
    if self.settings.add_help:
      body += '''
for idx in "${{_do_pp[@]}}"; do
  [[ $idx = 'a' ]] && continue
  if [[ ${{_do_sh[$idx]}} = "-h" || ${{_do_lo[$idx]}} = "--help" ]]; then
    printf -- "{template}" "${docname}"
    exit 0
  fi
done
'''.format(
        template='%s' if self.settings.script.doc.value.endswith('\n') else '%s\\n',
        docname=self.settings.script.doc.name,
      )
    if self.settings.add_version:
      body += '''
for idx in "${_do_pp[@]}"; do
  [[ $idx = 'a' ]] && continue
  if [[ ${_do_lo[$idx]} = "--version" ]]; then
    printf "%s\\n" "$version"
    exit 0
  fi
done
'''

    # setup $_lft
    body += '''
local i=0
while [[ $i -lt ${#_do_pp[@]} ]]; do
  _lft+=("$i")
  ((i++))
done
'''
    # run the parser
    body += '''
if ! {root} || [ ${{#_lft[@]}} -gt 0 ]; then
  _do_err
fi
'''.format(root=self.root_node.body)
    # defaults
    if len(self.leaf_nodes) > 0:
      body += '''
_do_def
'''

    # teardown
    if self.settings.add_teardown:
      body += '''
unset _do_av _do_sh _do_lo _do_ac _do_pn _lft _do_pp _do_pv _do_tm
unset -f _do_eith _do_oom _do_opt _do_req _do_cmd _do_sw _do_val _do_def \\
_do_err _do_long _do_shorts docopt
'''

    body += '''
return 0
'''
    return body
