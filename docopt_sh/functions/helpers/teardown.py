from .. import Function


class Teardown(Function):
  def __init__(self, settings):
    super(Teardown, self).__init__(settings, 'teardown')

  def include(self):
    return self.settings.add_teardown

  def __str__(self):
    script = '''
unset argv options_short options_long options_argcount param_names \\
parsed_params parsed_values left test_match
unset -f either oneormore optional required _command _switch _value \\
check defaults extras help error docopt \\
parse_argv parse_long parse_shorts setup teardown
'''
    return self.fn_wrap(script)
