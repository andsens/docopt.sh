from .. import Function
import hashlib


class Check(Function):

  def __init__(self, settings):
    super(Check, self).__init__(settings, 'check')
    self.digest = hashlib.sha256(settings.script.doc.value.encode('utf-8')).hexdigest()

  def include(self):
    return self.settings.add_doc_check

  def __str__(self):
    script = '''
local current_doc_hash
local digest="{digest}"
current_doc_hash=$(printf "%s" "${docname}" | shasum -a 256 | cut -f 1 -d " ")
if [[ $current_doc_hash != "$digest" ]]; then
  printf "The current usage doc (%s) does not match what the parser was generated with (%s)\\n" \\
    "$current_doc_hash" "$digest" >&2
  exit 1
fi
'''.format(docname=self.settings.script.doc.name, digest=self.digest)
    return self.fn_wrap(script)
