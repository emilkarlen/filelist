Test use the "Exactly" tool.

Install from PyPi:

> pip3 install exactly


NOTE!
Some test cases may fail because some
external programs used by the examples may not be found on the current OS.
E.g. /usr/bin/python.

The examples need some executable test programs to be generated first.
Generate them using:

> python3 make-executables.py all


Remove them using:

> python3 make-executables.py clean


Examples can be run using:

> exactly suite exactly.suite

or

> exactly suite intro/exactly.suite
> exactly suite readme-file-examples/exactly.suite
> exactly suite wiki/exactly.suite


or, if an executable has not been installed:

> python3 ../src/default-main-program-runner.py suite exactly.suite
