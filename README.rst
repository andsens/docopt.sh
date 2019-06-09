docopt.sh
=========

.. image:: https://travis-ci.org/andsens/docopt.sh.png?branch=master
    :target: https://travis-ci.org/andsens/docopt.sh

``docopt.sh`` is a bash argument parser generator.
Given a script it finds the ``docopt`` help text, parses it, generates a
matching parser in bash, and then inserts it back into the original script.

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
    docopt "$@"
    $ship && $move && printf "The %s is now moving to %d,%d at %d knots.\n" "$_name_" "$_x_" "$_y_" "$__speed"
    $ship && $shoot && printf "You shoot at %d,%d. It's a hit!\n" "$_x_" "$_y_"
    exit 0

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
    docopt "$@"
    $ship && $move && printf "The %s is now moving to %d,%d at %d knots.\n" "$_name_" "$_x_" "$_y_" "$__speed"
    $ship && $shoot && printf "You shoot at %d,%d. It's a hit!\n" "$_x_" "$_y_"
    exit 0

To try it our we run `naval_fate.sh`

.. code-block::

    $ ./naval_fate.sh ship Olympia move 1 5 --speed 8
    The Olympia is now moving to 1,5 at 8 knots.


Refreshing the parser
---------------------

``docopt.sh`` embeds a hash of the help text into the parser to ensure that the
two always match. In order to update the parser simply run ``docopt.sh`` again,
the existing parser will be replaced with a new one.
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

Commandline options
-------------------

The commandline options of ``docopt.sh`` mostly change _how_ the parser is
generated while options to ``docopt "$@"`` itself change the behavior of
the parser.

The commandline options are:

+----------------------+----------------------------------------------+
|        Option        |                 Description                  |
+======================+==============================================+
| ``--line-length N``  | Max line length when minifying.              |
|                      | Disable with ``0`` (default: 80)             |
+----------------------+----------------------------------------------+
| ``--library -l SRC`` | Generates the dynamic part of the parser and |
|                      | includes the static parts with `source SRC`. |
|                      | See `Library mode`_ for more details.        |
+----------------------+----------------------------------------------+
| ``--no-auto-params`` | Disable auto-detection of parser             |
|                      | generation parameters                        |
+----------------------+----------------------------------------------+
| ``--parser``         | Output the parser instead of inserting       |
|                      | it in the script                             |
+----------------------+----------------------------------------------+

Parser options
--------------

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
| ``$DOCOPT_TEARDOWN``        | Set to ``false`` to prevent cleanup of      |
|                             | $docopt_ variables (default: ``true``)      |
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


Variable name mapping
---------------------


Exiting with a usage message
----------------------------

Oftentimes additional verification of parameters is necessary (e.g. when an
option value is an enum). In those cases you can use ``docopt_error "message"``
in order to output a message for the user, followed by the short usage help
(i.e. without extended options), followed by ``exit 1``.


Library mode
------------

Testing
-------
