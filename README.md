# docopt.sh

This software is still in early alpha. Not for production use.

```
docopt.sh - Bash argument parser generator.
  This program looks for a docopt usage string
  in a script and appends a matching parser to it.

Usage:
  docopt.sh generate-library
  docopt.sh [options] [SCRIPT]

Options:
  --prefix PREFIX    Parameter variable name prefix [default: ]
  --line-length N    Max line length when minifying (0 to disable) [default: 80]
  --parser           Output parser instead of inserting it in the script
  --library -l PATH  Generates only the dynamic part of the parser and includes
                     the static parts from a file located at PATH,
                     use `generate-library` to create that file.
  -h --help          This help message
  --version          Version of this program

Notes:
  You can pass the script on stdin as well,
  docopt.sh will then output the modified script to stdout.

  If the script has a $version defined anywhere before the invocation of docopt
  --version will automatically output the value of that variable.
```
