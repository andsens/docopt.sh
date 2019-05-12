import hashlib
from .. import Function, bash_variable_name, bash_ifs_value
from ...doc import Option


class Main(Function):
  def __init__(self, settings, sorted_params):
    super(Main, self).__init__(settings, 'docopt')
    self.sorted_params = sorted_params

  @property
  def body(self):
    body = ''
    if self.settings.add_doc_check:
      body += '''
local current_doc_hash
local digest="{digest}"
current_doc_hash=$(printf "%s" "${docname}" | shasum -a 256 | cut -f 1 -d " ")
if [[ $current_doc_hash != "$digest" ]]; then
  printf "The current usage doc (%s) does not match what the parser was generated with (%s)\\n" \\
    "$current_doc_hash" "$digest" >&2
  exit 70
fi
'''.format(
        docname=self.settings.script.doc.name,
        digest=hashlib.sha256(self.settings.script.doc.value.encode('utf-8')).hexdigest()
      )
    # variables setup
    sorted_options = [o for o in self.sorted_params if type(o) is Option]
    body += '''
argv=("$@")
options_short=({options_short})
options_long=({options_long})
options_argcount=({options_argcount})
param_names=({param_names})
parsed_params=()
parsed_values=()
left=()
test_match=false
local var
for var in "${{param_names[@]}}"; do
  unset "$var"
done
'''.format(
      options_short=' '.join([bash_ifs_value(o.short) for o in sorted_options]),
      options_long=' '.join([bash_ifs_value(o.long) for o in sorted_options]),
      options_argcount=' '.join([bash_ifs_value(o.argcount) for o in sorted_options]),
      param_names=' '.join([bash_variable_name(p.name, self.settings.name_prefix) for p in self.sorted_params]),
    )
    # parse argv
    body += '''
local arg
while [[ ${#argv[@]} -gt 0 ]]; do
  if [[ ${argv[0]} == "--" ]]; then
    for arg in "${argv[@]}"; do
      parsed_params+=('a')
      parsed_values+=("$arg")
    done
    break
  elif [[ ${argv[0]} = --* ]]; then
    parse_long
  elif [[ ${argv[0]} == -* && ${argv[0]} != "-" ]]; then
    parse_shorts
  else
'''
    if self.settings.options_first:
      body += '''
    for arg in "${argv[@]}"; do
      parsed_params+=('a')
      parsed_values+=("$arg")
    done
    break
'''
    else:
      body += '''
    parsed_params+=('a')
    parsed_values+=("${argv[0]}")
    argv=("${argv[@]:1}")
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
for idx in "${{parsed_params[@]}}"; do
  [[ $idx == 'a' ]] && continue
  if [[ ${{options_short[$idx]}} == "-h" || ${{options_long[$idx]}} == "--help" ]]; then
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
for idx in "${parsed_params[@]}"; do
  [[ $idx == 'a' ]] && continue
  if [[ ${options_long[$idx]} == "--version" ]]; then
    printf "%s\\n" "$version"
    exit 0
  fi
done
'''

    # setup $left
    body += '''
local i=0
while [[ $i -lt ${#parsed_params[@]} ]]; do
  left+=("$i")
  ((i++))
done
'''
    # run the parser
    body += '''
if ! root || [ ${#left[@]} -gt 0 ]; then
  error
fi
'''
    # defaults
    if len(self.sorted_params) > 0:
      body += '''
defaults
'''

    # teardown
    if self.settings.add_teardown:
      body += '''
unset argv options_short options_long options_argcount param_names \\
parsed_params parsed_values left test_match
unset -f either oneormore optional required _command _switch _value \\
check defaults extras help error docopt \\
parse_argv parse_long parse_shorts setup teardown
'''

    body += '''
return 0
'''
    return body
