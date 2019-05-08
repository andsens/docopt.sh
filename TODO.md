Run all generated parsers through shellcheck
Handle special chars in var names (compare with normal docopt behavior)
Handle function & variable collision
Write testcases for detection of variable naming collision
Has usage to ensure parser is up to date
Replace double == with single =
Respect help better & show short usage
Add version of docopt.sh to hash & inform user whether update made any changes
Account for presence of version variable in hash
Don't wait for stdin when it is a tty
Check for version up until docopt invocation (if there is any, otherwise just the whole script)
Check that docopt invocation is after usage doc
