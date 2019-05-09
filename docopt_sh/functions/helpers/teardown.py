from .. import Function


class Teardown(Function):
  def __init__(self, no_teardown):
    super(Teardown, self).__init__('teardown')
    self.no_teardown = no_teardown

  def include(self):
    return not self.no_teardown

  def __str__(self):
    script = '''
unset argv options_short options_long options_argcount param_names \\
parsed_params parsed_values left test_match
unset -f either oneormore optional required _command _switch _value \\
check defaults extras help error docopt \\
parse_argv parse_long parse_shorts setup teardown
'''
    return self.fn_wrap(script)
