Run all generated parsers through shellcheck
Handle special chars in var names (compare with normal docopt behavior)
Has usage to ensure parser is up to date
Replace double == with single =
Respect help better & show short usage
Add version of docopt.sh to hash & inform user whether update made any changes
Account for presence of version variable in hash
Don't wait for stdin when it is a tty
Check for version up until docopt invocation (if there is any, otherwise just the whole script)
Check that docopt invocation is after usage doc
Prefix names with docopt
Check for docopt_* function/variable name collision, test it
Convert test_match into parameter
--add-version    Add --version despite no $version being present
Add library version that allows inclusion from multiple scripts
