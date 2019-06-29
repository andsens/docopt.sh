docopt.sh
=========

.. image:: https://travis-ci.org/andsens/docopt.sh.png?branch=master
    :target: https://travis-ci.org/andsens/docopt.sh

``docopt.sh`` is a bash argument parser generator.
Given a script it finds the ``docopt`` help text, parses it, generates a
matching parser in bash, and then inserts it back into the original script.
The resulting script is completely dependencyless (save for bash itself)
and can be shipped without any additional files.

The parser is compatible with bash 3.2+.

* `Installation`_
* `Quick example`_
* `Refreshing the parser`_
* `Parser output`_
* `Commandline options`_
* `Parser options`_
* `Exiting with a usage message`_
* `Library mode`_
* `Testing`_


Installation
------------

Albeit ``docopt.sh`` outputs bash the program itself is written in python.
Install ``docopt.sh`` using pip:

.. code-block::

    pip3 install docopt-sh


Quick example
-------------

Here is an abbreviated version of `Naval Fate <http://try.docopt.org/>`_.

.. code-block:: sh

    #!/usr/bin/env bash

    DOC="Naval Fate.

    Usage:
      naval_fate.py ship <name> move <x> <y> [--speed=<kn>]
      naval_fate.py ship shoot <x> <y>

    Options:
      --speed=<kn>  Speed in knots [default: 10].
      --moored      Moored (anchored) mine.
      --drifting    Drifting mine."

    naval_fate() {
      eval "$(docopt "$@")"
      $ship && $move && printf "The %s is now moving to %d,%d at %d knots.\n" "$_name_" "$_x_" "$_y_" "$__speed"
      $ship && $shoot && printf "You shoot at %d,%d. It's a hit!\n" "$_x_" "$_y_"
      return 0
    }
    naval_fate "$@"

We can use ``docopt.sh`` to insert a matching parser:

.. code-block::

    $ docopt.sh naval_fate.sh
    naval_fate.sh has been updated

The file will now look like this:

.. code-block:: sh

    #!/usr/bin/env bash
    DOC="Naval Fate.

    Usage:
      naval_fate.py ship <name> move <x> <y> [--speed=<kn>]
      naval_fate.py ship shoot <x> <y>

    Options:
      --speed=<kn>  Speed in knots [default: 10].
      --moored      Moored (anchored) mine.
      --drifting    Drifting mine."
    # docopt parser below, refresh this parser with `docopt.sh naval_fate.sh`
    docopt(){ docopt_doc=${DOC:0:237}; docopt_usage=${DOC:13:97}
    docopt_digest=79f25; docopt_shorts=(''); docopt_longs=(--speed)
    docopt_argcount=(1); docopt_param_names=(__speed _name_ _x_ _y_ ship move shoot)
    docopt_node_0(){ docopt_value __speed 0; }; docopt_node_1(){
    ... more code ...
    done; if ! docopt_required root || [ ${#docopt_left[@]} -gt 0 ]; then
    docopt_error; fi; return 0; }
    # docopt parser above, complete command for generating this parser is `docopt.sh naval_fate.sh`

    naval_fate() {
      eval "$(docopt "$@")"
      $ship && $move && printf "The %s is now moving to %d,%d at %d knots.\n" "$_name_" "$_x_" "$_y_" "$__speed"
      $ship && $shoot && printf "You shoot at %d,%d. It's a hit!\n" "$_x_" "$_y_"
      return 0
    }
    naval_fate "$@"

To try it out we run ``naval_fate.sh``

.. code-block::

    $ ./naval_fate.sh ship Olympia move 1 5 --speed 8
    The Olympia is now moving to 1,5 at 8 knots.

Note that the variables ``$ship``, ``$move``, etc. are not set globally, but
rather contained to the scope of the invoking function.
You are however not restricted to calling ``eval "$(docopt "$@")"`` from a
function, calling docopt outside of functions will work just fine and the
variables will then be defined globally.

Refreshing the parser
---------------------

``docopt.sh`` embeds a hash of the help text into the parser to ensure that the
two always match. In order to update the parser, simply run ``docopt.sh``
again. The existing parser will be replaced with a new one.
If the parser was generated with any particular options, these options will be
re-applied unless instructed otherwise with ``--no-auto-params``
(``docopt.sh`` also embeds the command line options it was used with).

.. code-block::

    $ docopt.sh --line-length 120 naval_fate.sh
    naval_fate.sh has been updated.
    $ docopt.sh naval_fate.sh
    Adding `--line-length=120` from parser generation parameters that were detected
    in the script. Use --no-auto-params to disable this behavior.
    The parser in naval_fate.sh is already up-to-date.

Note that once you have generated the parser, you can move the codeblock to
any other place in your script. The generator will automatically find the code
and replace it in-place.

Parser output
-------------

Names of arguments, commands, and options are mapped by replacing everything
that is not an alphanumeric character or an underscore with an underscore.
This means ``--speed`` becomes ``$__speed``, ``-f`` becomes ``$_f``, and
``<name>`` becomes ``_name_``, while ``NAME`` stays as ``$NAME`` and
``set`` stays as ``$set``.

Commands and switches (options without arguments) become ``true`` or ``false``.
If a command or switch can be specified more than once, the value will be an
integer that has been incremented the number of times the parameter was
specified.

Arguments and options with values get the values as strings.
If an argument or option with a value can be specified more that once,
the value will be an array of strings.

To clarify, given this doc and invocation:

.. code-block::

    Usage:
      program -v... -s --val=VAL multicmd... command ARG ARGS...

    $ program -vvv -s --val XY multicmd multicmd command A 1 2 3

The variables and their values will be:

.. code-block::

    _v=3 # -vvv
    _s=true # -s
    __val=XY # --val XY
    __val=true # --val
    multicmd=2 # multicmd multicmd
    command=true # command
    ARG=A # A
    ARGS=(1 2 3) # 1 2 3

You can use ``$DOCOPT_PREFIX`` to change the above output by prefixing the
variable names. See `parser options`_ for more details.

Commandline options
-------------------

The commandline options of ``docopt.sh`` only change _how_ the parser is
generated while options to ``eval "$(docopt "$@")"`` itself change the
behavior of the parser.

The commandline options are:

+-------------------------+----------------------------------------------+
|         Option          |                 Description                  |
+=========================+==============================================+
| ``--line-length -n N``  | Max line length when minifying.              |
|                         | Disable with ``0`` (default: 80)             |
+-------------------------+----------------------------------------------+
| ``--library -l SRC``    | Generates the dynamic part of the parser and |
|                         | includes the static parts with `source SRC`. |
|                         | See `Library mode`_ for more details.        |
+-------------------------+----------------------------------------------+
| ``--no-auto-params -P`` | Disable auto-detection of parser             |
|                         | generation parameters                        |
+-------------------------+----------------------------------------------+
| ``--parser -p``         | Output the parser instead of inserting       |
|                         | it in the script                             |
+-------------------------+----------------------------------------------+
| ``--help -h``           | Show the help screen                         |
+-------------------------+----------------------------------------------+
| ``--version``           | Show docopt.sh version                       |
+-------------------------+----------------------------------------------+

Parser options
--------------

Parser options change the behavior of the parser in various ways. They all have
in common that they must be specified *before* invoking
``eval "$(docopt "$@")"``.

+-----------------------------+---------------------------------------------+
|           Option            |                 Description                 |
+=============================+=============================================+
| ``$DOCOPT_PROGRAM_VERSION`` | The string to print when --version is       |
|                             | specified (default: none)                   |
+-----------------------------+---------------------------------------------+
| ``$DOCOPT_ADD_HELP``        | Set to `false` to not print usage on --help |
|                             | (default: ``true``)                         |
+-----------------------------+---------------------------------------------+
| ``$DOCOPT_OPTIONS_FIRST``   | Set to ``true`` to fail when options are    |
|                             | specified after arguments/commands          |
|                             | (default: false)                            |
+-----------------------------+---------------------------------------------+
| ``$DOCOPT_PREFIX``          | Prefixes all variable names with the        |
|                             | specified value (default: ``""``)           |
+-----------------------------+---------------------------------------------+
| ``$DOCOPT_DOC_CHECK``       | Set to ``false`` to disable checking        |
|                             | whether the parser matches the doc          |
|                             | (default: ``true``)                         |
+-----------------------------+---------------------------------------------+
| ``$DOCOPT_LIB_CHECK``       | Set to ``false`` to disable checking        |
|                             | whether the library version and the         |
|                             | docopt parser version match                 |
|                             | (default: ``true``)                         |
|                             | See `Library mode`_ for more details.       |
+-----------------------------+---------------------------------------------+

Exiting with a usage message
----------------------------

Oftentimes additional verification of parameters is necessary (e.g. when an
option value is an enum). In those cases you can use ``docopt_exit "message"``
in order to output a message for the user, the function automatically appends
a short usage help (i.e. without extended options) and then exits with
code ``1``.

Library mode
------------

Instead of inlining the entirety of the parser in your script, you can move the
static parts to an external file and only insert the dynamic part into your
script.

To generate the library, run ``docopt.sh generate-library > DEST``.
Note that the output is written to ``stdout``, so make sure to add that
redirect.

Once a library has been generated you can insert the dynamic part of your
parser into your script with ``docopt.sh --library DEST SCRIPT``. The generator
will then automatically add a `source DEST` to the parser. Make sure to quote
your library path if it contains spaces like so
``docopt.sh --library '"/path with spaces/docopt-lib.sh"'``.
Once that is done, you do not need to specify ``--library`` on subsequent
refreshes of the parser, ``docopt.sh`` will automatically glean the previously
used parameters from your script and re-apply them.

Note that ``--library`` can be any valid bash expression, meaning you can use
things like ``"$(dirname "$0")"``.

On every invocation docopt checks that the library version and the version of
the dynamic part in the script match. The parser exits with an error if that
is not the case.

Developers
----------

Testing
~~~~~~~

``docopt.sh`` uses pytest_ for testing. You can run the testsuite by running
``pytest``.

All usecases_ from the original docopt are used to validate correctness.
Per default pytest uses the bash version that is installed on the system to
run the tests.

However, you can specify multiple alternate versions using
``--bash-version <versions>``, where ``<versions>`` is a comma-separated list
of bash version of the form ``3.2,4.0,4.1`` etc.. These versions need to be
downloaded and compiled first though, the process has been fully automated with
``get_bash.py``, the scripts downloads, extracts, configures, and compiles the
specified bash versions in the ``tests/bash-versions`` folder.
Use ``--bash-version all`` to test with all the bash versions that are
installed.


.. _pytest: https://pytest.org/
.. _usecases: https://github.com/andsens/docopt.sh/blob/c254d766a8eda8537bd5438b6ff22e005de4b586/tests/usecases.txt
