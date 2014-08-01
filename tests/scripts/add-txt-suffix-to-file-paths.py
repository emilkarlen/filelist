# -*- coding: utf-8 -*-

import sys
import re


ignored_line_re_string = "\s*(#.*)?$"
ignored_line_re = re.compile(ignored_line_re_string)


for line in sys.stdin:
    line = line.rstrip()
    if ignored_line_re.match(line):
        continue
    if line[0] == "@":
        print(line)
        continue
    print(line + ".txt")
